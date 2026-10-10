"""Montage du compte IA / SEO Radius (iafortous) : script + voix alignée -> timeline TechShort
-> rendu Remotion -> mixage (voix devant, musique basse, bruitages discrets).

Chaque segment du script peut porter un "visual" (scène). Un segment sans visual prolonge la
scène précédente. Les révélations internes (éléments d'une liste) peuvent être calées sur un
mot prononcé avec "at".
"""
from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from . import motion as M

ROOT = Path(__file__).resolve().parent.parent
FPS = 30
TRANS = ["up", "zoom", "left", "up", "zoom"]
ACCENTS = {"ia": "#D4FF3A", "seo": "#3AD8FF"}


def f(t: float) -> int:
    return int(round(t * FPS))


def _n(w: str) -> str:
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def _words(tl: list) -> list[dict]:
    out = []
    for si, x in enumerate(tl):
        for w in x["words"]:
            out.append({**w, "seg": si, "n": _n(w["w"])})
    return out


def _find(words: list, token: str, after: float, before: float) -> float | None:
    key = _n(token.split()[0]) if token.strip() else ""
    for w in words:
        if after - 0.01 <= w["start"] < before and key and (w["n"] == key or (len(key) >= 4 and w["n"].startswith(key))):
            return w["start"]
    return None


def build(script: dict, voice: dict, work: Path, rng: random.Random) -> tuple[dict, list, dict]:
    pub = work / "pub"
    if pub.exists():
        shutil.rmtree(pub)
    (pub / "fonts").mkdir(parents=True)
    (pub / "img").mkdir()
    for ff in (ROOT / "fonts").glob("*.woff2"):
        shutil.copy(ff, pub / "fonts" / ff.name)

    tl = voice["timeline"]
    total = tl[-1]["slot_end"]
    words = _words(tl)
    theme = script.get("theme", "ia")
    accent = script.get("accent") or ACCENTS.get(theme, ACCENTS["ia"])
    hook_end = tl[0]["slot_end"] if script.get("hook_text") else 0.0
    cues: list = [(0.0, "boom")]

    # hook : les mots du 1er segment s'écrivent en gros au moment où ils sont dits
    hook = None
    if script.get("hook_text"):
        hw = [{"w": w["w"], "from": f(w["start"])} for w in tl[0]["words"]]
        hook = {"text": script["hook_text"], "from": 0, "to": f(hook_end), "words": hw}

    # scènes
    starts = []
    for si, (seg, x) in enumerate(zip(script["segments"], tl)):
        if seg.get("visual"):
            t0 = max(x["start"] - 0.12, 0.0)
            if si == 0 and hook:  # pas de scène sous le hook : elle démarre à sa sortie
                continue
            starts.append((si, t0, seg["visual"], seg))
    if not starts:  # sécurité : un titre par défaut
        starts.append((1 if len(tl) > 1 else 0, hook_end, {"kind": "title", "text": script.get("title", "")},
                       script["segments"][0]))
    # la 1re scène commence pile à la sortie du hook
    if hook:
        si, _, vis, seg = starts[0]
        starts[0] = (si, max(hook_end - 0.1, 0.0), vis, seg)
    scenes, last_trans = [], None
    for k, (si, t0, vis, seg) in enumerate(starts):
        t1 = starts[k + 1][1] if k + 1 < len(starts) else total
        vis = dict(vis)
        kind = vis.pop("kind", "title")
        trans = "flash" if seg.get("sfx") else rng.choice([t for t in TRANS if t != last_trans])
        last_trans = trans
        marks = []
        for item_at in vis.pop("at", []) or []:
            ts = _find(words, str(item_at), t0, t1)
            marks.append(f(ts - t0) if ts is not None else None)
        # éléments sans mot repéré : répartis entre les repères connus
        if marks and any(m is None for m in marks):
            dur = f(t1 - t0)
            n = len(marks)
            marks = [m if m is not None else 8 + int((dur - 20) * i / max(1, n)) for i, m in enumerate(marks)]
        if kind == "shot" and vis.get("src"):
            src = (work / vis["src"]).resolve()
            if src.exists():
                dst = pub / "img" / src.name
                shutil.copy(src, dst)
                vis["src"] = f"img/{src.name}"
            else:
                kind, vis = "title", {"text": vis.get("title", script.get("title", ""))}
        scenes.append({"from": f(t0), "dur": max(1, f(t1) - f(t0)), "kind": kind, "trans": trans,
                       "marks": marks, "data": vis})
        if k > 0 or not hook:
            cues.append((t0, "impact" if trans == "flash" else ("whoosh" if trans == "left" else "swoosh")))
        if kind == "list":
            cues += [(t0 + m / FPS, "pop") for m in marks]
        if kind == "stat":
            cues.append((t0 + 0.15, "riser"))

    # sous-titres (pas pendant le hook, déjà écrit en gros)
    emph = {_n(w) for sg in script["segments"] for w in sg.get("emphasis", [])}
    groups = []
    for si, x in enumerate(tl):
        if si == 0 and hook:
            continue
        cur: list = []
        for w in x["words"]:
            cur.append(w)
            if w["w"][-1] in ".,!?…:;" or len(cur) >= 3 or (len(cur) == 2 and len(cur[0]["w"] + w["w"]) > 13):
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
    g_props = [{"from": f(g[0]["start"]), "to": f(g[-1]["end"]) + 2,
                "words": [{"w": w["w"], "from": f(w["start"]), "to": f(w["end"]), "hl": _n(w["w"]) in emph}
                          for w in g]} for g in groups]

    stamps = []
    for seg, x in zip(script["segments"], tl):
        if seg.get("stamp"):
            at = x["start"] + (x["end"] - x["start"]) * 0.35
            stamps.append({"text": seg["stamp"], "from": f(at), "to": f(min(at + 1.5, x["slot_end"]))})
            cues.append((at, "impact"))

    props = {"durationInFrames": f(total) + 1, "hook": hook, "scenes": scenes, "groups": g_props,
             "stamps": stamps, "accent": accent, "theme": theme}
    (work / "timeline.json").write_text(json.dumps(props, ensure_ascii=False))
    music = M.pick_music({"music": script.get("music", "pote"), "tone": "pote"}, total, rng)
    cues = sorted([c for c in cues if c[1]], key=lambda c: c[0])
    thin, last = [], -9.0
    for t, kind in cues:
        if t - last >= 0.35 or kind in ("impact", "boom"):
            thin.append((t, kind))
            last = t
    return props, thin, music


def render_video(work: Path, out: Path) -> None:
    M.ensure_node_modules()
    cmd = ["npx", "remotion", "render", "src/index.tsx", "TechShort", str(out),
           f"--props={work / 'timeline.json'}", f"--public-dir={work / 'pub'}",
           "--muted", "--codec=h264", "--crf=20", f"--concurrency={min(2, os.cpu_count() or 1)}", "--log=error",
           "--timeout=120000"]
    if Path(M.CHROME).exists():
        cmd.append(f"--browser-executable={M.CHROME}")
    subprocess.run(cmd, cwd=M.REMOTION, check=True, timeout=int(os.environ.get("TF_REMOTION_TIMEOUT", "2100")))


def render(script: dict, voice: dict, work: Path, out_path: Path, seed: int = 0) -> dict:
    work, out_path = Path(work).resolve(), Path(out_path).resolve()
    rng = random.Random(seed)
    props, cues, music = build(script, voice, work, rng)
    silent = work / "video_silent.mp4"
    render_video(work, silent)
    hook_end = voice["timeline"][0]["slot_end"] if script.get("hook_text") else 2.5
    audio = M.mix(Path(voice["path"]), music, voice["duration"], cues, work, hook_end)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(audio), "-map", "0:v",
                    "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "6M",
                    "-bufsize", "12M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
                    "-movflags", "+faststart", str(out_path)], check=True)
    return {"path": str(out_path), "duration": voice["duration"], "scenes": len(props["scenes"]),
            "music": {k: music[k] for k in ("file", "bpm", "offset")}, "sfx": len(cues),
            "engine": "remotion TechShort"}
