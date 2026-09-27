"""Minutage réel des mots : transcription de la voix générée (faster-whisper) puis
alignement sur le texte du script. Remplace les temps estimés de voice.py, pour que
chaque image et chaque sous-titre tombent exactement sur le mot prononcé.
"""
from __future__ import annotations

import difflib
import os
import re
import unicodedata

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")


def _n(w: str) -> str:
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def _transcribe(path: str) -> list[dict]:
    from faster_whisper import WhisperModel  # type: ignore
    model = WhisperModel(os.environ.get("TF_WHISPER", "small"), device="cpu", compute_type="int8")
    segs, _ = model.transcribe(path, language="fr", word_timestamps=True, vad_filter=False,
                               condition_on_previous_text=False)
    out = []
    for s in segs:
        for w in s.words or []:
            # whisper colle parfois l'apostrophe : "l 'air" -> deux mots, on garde tel quel
            for part in w.word.strip().split():
                out.append({"n": _n(part), "s": float(w.start), "e": float(w.end)})
    return [x for x in out if x["n"]]


def align(voice: dict) -> dict:
    """Corrige voice['timeline'][i]['words'] en place avec les vrais temps. Sans faster-whisper
    ou en cas d'échec, les temps estimés sont conservés."""
    try:
        heard = _transcribe(voice["path"])
    except Exception as exc:  # pas bloquant
        print(f"[align] alignement impossible ({exc}), temps estimés conservés")
        voice["aligned"] = False
        return voice
    # mots du script, découpés comme whisper (apostrophes séparées)
    script_words = []
    for si, seg in enumerate(voice["timeline"]):
        for wi, w in enumerate(seg["words"]):
            parts = [p for p in re.split(r"[’']", w["w"]) if _n(p)] or [w["w"]]
            for p in parts:
                script_words.append((si, wi, _n(p)))
    a = [x[2] for x in script_words]
    b = [x["n"] for x in heard]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    starts: dict = {}
    ends: dict = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            for k in range(i2 - i1):
                key = script_words[i1 + k][:2]
                starts.setdefault(key, heard[j1 + k]["s"])
                ends[key] = heard[j1 + k]["e"]
        elif tag == "replace" and j2 > j1:  # blocs de tailles différentes : répartition linéaire
            s0, e0 = heard[j1]["s"], heard[j2 - 1]["e"]
            n = i2 - i1
            for k in range(n):
                key = script_words[i1 + k][:2]
                starts.setdefault(key, s0 + (e0 - s0) * k / n)
                ends[key] = s0 + (e0 - s0) * (k + 1) / n
    matched = 0
    for si, seg in enumerate(voice["timeline"]):
        ws = seg["words"]
        for wi, w in enumerate(ws):
            if (si, wi) in starts:
                w["start"], w["end"] = round(starts[(si, wi)], 3), round(max(ends[(si, wi)], starts[(si, wi)] + 0.05), 3)
                matched += 1
        # mots non entendus : interpolation entre voisins alignés
        known = [i for i, w in enumerate(ws) if (si, i) in starts]
        for i, w in enumerate(ws):
            if (si, i) in starts:
                continue
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            lo = ws[prev]["end"] if prev is not None else seg["start"]
            hi = ws[nxt]["start"] if nxt is not None else seg["end"]
            w["start"] = round(lo, 3)
            w["end"] = round(max(lo + 0.05, min(hi, lo + 0.4)), 3)
        # monotonie
        for i in range(1, len(ws)):
            if ws[i]["start"] < ws[i - 1]["start"]:
                ws[i]["start"] = ws[i - 1]["start"]
        if ws:
            seg["start"] = min(seg["start"], ws[0]["start"]) if seg.get("index") == 0 else ws[0]["start"]
            seg["end"] = ws[-1]["end"]
    total = sum(len(s["words"]) for s in voice["timeline"])
    voice["aligned"] = round(matched / max(1, total), 3)
    print(f"[align] {matched}/{total} mots alignés sur la voix réelle")
    return voice
