"""Audit automatique d'une vidéo @iafortous, pour s'améliorer en continu.

    python -m factory.audit runs/ia/<stamp>

Mesure : durée, silence d'ouverture, débit (mots/min de parole), justesse de la prononciation
(la voix est retranscrite par Whisper puis comparée au script : prix et nombres compris),
mots mal prononcés. Écrit runs/ia/<stamp>/audit.json, ajoute une ligne à audits_ia.jsonl et
signale les mots mal compris sur plusieurs vidéos (candidats pour config/prononciation.json).
"""
from __future__ import annotations

import collections
import difflib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = Path(os.environ.get("TF_AUDIT_LOG", ROOT / "audits_ia.jsonl"))
# repères (retours de Bill) : voix claire, pas trop rapide, prix bien dits
# débit en caractères prononcés par seconde de parole (pauses exclues). Estelle brute = 23,5 car./s,
# jugée un chouïa trop rapide par Bill : on vise 23 à 25,5 (texte prononcé, nombres en lettres).
CPS_MAX = 25.5   # mesuré : voix brute 27,2 (trop rapide selon Bill), voix à 0,94 = 25,2
CPS_MIN = 19.0
# voix Gemini « Kore » (depuis le 26/10/2026) : débit naturel plus posé que Kyutai. Fourchette large
# en attendant les premières mesures (à resserrer après une dizaine de vidéos, cf. audits_ia.jsonl).
CPS_BY_ENGINE = {"gemini": (14.0, 24.0)}
ACC_MIN = 0.93      # part des mots du script retrouvés à l'écoute
DUR = (60, 100)


def _speech_seconds(path: str) -> tuple[float, float, float]:
    """(durée totale, temps de parole, silence d'ouverture)."""
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                 capture_output=True, text=True).stdout.strip() or 0)
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "silencedetect=n=-40dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    sil = [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", err)]
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    lead = sil[0] if starts and starts[0] < 0.05 and sil else 0.0
    return total, max(1.0, total - sum(sil)), lead


def _tokens(text: str) -> list[str]:
    from .align import _n
    from .pronounce import speakable
    from .voice import _plain
    words = re.split(r"[\s’'\-]+", speakable(_plain(text)))
    return [w for w in (_n(x) for x in words) if w]


def audit(run: Path) -> dict:
    from .align import _transcribe
    script = json.loads((run / "script.json").read_text())
    voice = json.loads((run / "voice.json").read_text())
    total, speech, lead = _speech_seconds(voice["path"])
    ref = [t for seg in script["segments"] for t in _tokens(seg["text"])]
    heard_raw = _transcribe(voice["path"])
    heard = []
    for h in heard_raw:  # whisper écrit parfois "300" : on le remet en lettres comme le script
        heard += _tokens(h["n"]) if re.search(r"\d", h["n"]) else [h["n"]]
    sm = difflib.SequenceMatcher(a=ref, b=heard, autojunk=False)
    ok = sum(b.size for b in sm.get_matching_blocks())
    issues = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete") and i2 > i1:
            if tag == "delete" and set(ref[i1:i2]) <= {"euros", "euro", "pour", "cent", "et"}:
                continue  # whisper écrit "€" ou "%" : pas une faute de prononciation
            issues.append({"dit": " ".join(ref[i1:i2]), "entendu": " ".join(heard[j1:j2])})
    words = len(ref)
    from .pronounce import speakable
    from .voice import _plain
    lex = None
    if voice.get("engine") == "gemini":
        from .voice import GEMINI_LEXICON as lex
    chars = sum(len(speakable(_plain(seg["text"]), lexicon_file=lex)) for seg in script["segments"])
    cps = round(chars / speech, 1)
    acc = round(ok / max(1, words), 3)
    alerts = []
    cps_min, cps_max = CPS_BY_ENGINE.get(voice.get("engine"), (CPS_MIN, CPS_MAX))
    if cps > cps_max:
        alerts.append(f"débit {cps} car./s : trop rapide (max {cps_max})")
    if cps < cps_min:
        alerts.append(f"débit {cps} car./s : trop lent (min {cps_min})")
    if acc < ACC_MIN:
        alerts.append(f"prononciation {acc:.0%} des mots compris (min {ACC_MIN:.0%})")
    if lead < 0.3:
        alerts.append("la voix démarre trop tôt (moins de 0,3 s après l'affiche)")
    if not DUR[0] <= total <= DUR[1]:
        alerts.append(f"durée {total:.0f} s hors cible {DUR[0]} à {DUR[1]} s")
    res = {"stamp": run.name, "duration": round(total, 1), "lead": round(lead, 2), "cps": cps,
           "accuracy": acc, "engine": voice.get("engine"), "issues": issues[:25], "alerts": alerts}
    (run / "audit.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    with LOG.open("a") as f:
        f.write(json.dumps({k: res[k] for k in ("stamp", "duration", "lead", "cps", "accuracy", "engine", "alerts")}
                           | {"issues": issues[:12]}, ensure_ascii=False) + "\n")
    return res


def recurring(last: int = 15, min_count: int = 2) -> list[tuple[str, int]]:
    """Mots du script mal compris dans au moins min_count des derniers audits."""
    if not LOG.exists():
        return []
    lines = [json.loads(x) for x in LOG.read_text().splitlines() if x.strip()][-last:]
    c: collections.Counter = collections.Counter()
    for a in lines:
        seen = set()
        for it in a.get("issues", []):
            for w in it["dit"].split():
                if len(w) >= 3:
                    seen.add(w)
        c.update(seen)
    return [(w, n) for w, n in c.most_common() if n >= min_count]


if __name__ == "__main__":
    r = audit(Path(sys.argv[1]).resolve())
    print(f"AUDIT {r['stamp']} : {r['duration']} s, débit {r['cps']} car./s, "
          f"prononciation {r['accuracy']:.0%}, silence d'ouverture {r['lead']} s")
    for a in r["alerts"]:
        print(" ALERTE", a)
    for it in r["issues"][:12]:
        print(f" écart : dit « {it['dit']} » / entendu « {it['entendu']} »")
    rec = recurring()
    if rec:
        print("MOTS MAL COMPRIS SUR PLUSIEURS VIDÉOS (candidats au lexique) :",
              ", ".join(f"{w} ({n}x)" for w, n in rec[:10]))
