"""Montage v3 : timeline JSON -> rendu Remotion (moteur d'OpenMontage) -> mixage audio.

Python décide QUOI montrer et QUAND (plans calés sur la parole et sur le tempo de la
musique, transitions, étalonnage, habillage, bruitages). La composition Remotion
remotion/src/AnimeShort.tsx dessine tout (motion design, transitions, sous-titres).
"""
from __future__ import annotations

import json
import math
import os
import random
import shutil
import subprocess
from pathlib import Path

from . import assets as A
from . import sfx as SFX
from .render import _compose_still, _norm, plan_shots

ROOT = Path(__file__).resolve().parent.parent
REMOTION = ROOT / "remotion"
FPS = 30
CHROME = os.environ.get("TF_CHROME", "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")

TONE_GRADE = {"pote": "normal", "hype": "vivid", "conteur": "cinematic", "pose": "bw"}
TONE_PARTICLES = {"pote": ("fireflies", "#FFE082"), "hype": ("sparkles", "#FFD400"),
                  "conteur": ("mist", "#B0C4DE"), "pose": ("petals", "#F8BBD0")}
MUSIC_FOR = {"pote": ["pote"], "hype": ["hype"], "conteur": ["mystere", "conteur"],
             "pose": ["triste", "pose"], "mystere": ["mystere"], "triste": ["triste"],
             "hype2": ["hype"], "fun": ["fun", "pote"], "epic": ["epic", "hype"]}


def f(t: float) -> int:
    return int(round(t * FPS))


# ------------------------------------------------------------------ musique
def pick_music(script: dict, duration: float, rng: random.Random) -> dict:
    lib = json.loads((ROOT / "music" / "library.json").read_text())
    want = script.get("music") or script.get("tone", "pote")
    if want in ("hype2",):  # compat : nom de fichier explicite
        cands = [x for x in lib if x["file"] == "hype2.mp3"]
    else:
        tags = MUSIC_FOR.get(want, [want])
        cands = [x for x in lib if any(t in x["moods"] for t in tags)] or lib
    m = dict(rng.choice(cands))
    start = m["start"]
    if start + duration + 1 > m["duration"]:
        start = max(0.0, m["duration"] - duration - 1)
    m["offset"] = start
    m["beats_local"] = [b - start for b in m["beats"] if start <= b <= start + duration + 1]
    return m


def snap(t: float, beats: list[float], tol: float = 0.22) -> float:
    if not beats:
        return t
    b = min(beats, key=lambda x: abs(x - t))
    return b if abs(b - t) <= tol else t


# ------------------------------------------------------------------ timeline
def build(script: dict, voice: dict, index: dict, work: Path, rng: random.Random) -> tuple[dict, list, dict]:
    pub = work / "pub"
    if pub.exists():
        shutil.rmtree(pub)
    (pub / "fonts").mkdir(parents=True)
    (pub / "img").mkdir()
    for ff in ("Anton-Regular.ttf", "Montserrat-ExtraBold.ttf"):
        shutil.copy(ROOT / "fonts" / ff, pub / "fonts" / ff)
    shutil.copy(ROOT / "assets" / "grain.png", pub / "grain.png")
    shutil.copy(ROOT / "assets" / "avatar.png", pub / "avatar.png")

    tl = voice["timeline"]
    total = tl[-1]["slot_end"]
    tone = script.get("tone", "pote")
    music = pick_music(script, total, rng)
    beats = music["beats_local"]

    # 1) plan de base (synchro des noms) puis montage rapide du hook
    base = plan_shots(script, tl, index, rng)
    hook_end = tl[0]["slot_end"] if script.get("hook_text") else 0
    shots: list[dict] = []
    if hook_end:
        n = max(3, round(hook_end / 0.7))
        main = script["animes"][0]
        for i in range(n):
            shots.append({"start": hook_end * i / n, "end": hook_end * (i + 1) / n, "anime": main,
                          "kind": "any", "character": None, "fx": "hook" if i == 0 else None,
                          "role": "hook"})
        shots += [s for s in base if s["start"] >= hook_end - 0.05]
        if shots and len(shots) > n and shots[n]["start"] > hook_end + 0.05:
            shots[n]["start"] = hook_end
    else:
        shots = base
    # 2) coupes non liées à un nom : calées sur le tempo
    for i in range(1, len(shots)):
        s = shots[i]
        if s.get("role") == "hook" or s.get("character"):
            continue
        t = snap(s["start"], beats)
        if shots[i - 1]["start"] + 0.5 < t < s["end"] - 0.5:
            shots[i - 1]["end"] = t
            s["start"] = t

    # 3) images, transitions, étalonnage
    seg_of = lambda t: next((k for k, x in enumerate(tl) if x["start"] - 0.01 <= t < x["slot_end"]), len(tl) - 1)
    used: list = []
    props_shots, cues = [], [(0.0, "boom")]
    last_trans = "cut"
    for k, s in enumerate(shots):
        img = A.pick(index, s.get("anime"), s.get("kind", "any"), s.get("character"), used)
        if not img:
            continue
        name = f"img/s{k:03d}.jpg"
        _compose_still(img, pub / name, rng, "lines" if s.get("fx") == "hook" else "auto")
        seg = script["segments"][seg_of(s["start"] + 0.05)]
        role = s.get("role")
        if role == "hook":
            grade = "bw"
            trans = "cut" if k == 0 else rng.choice(["flash", "glitch", "whip"])
        else:
            grade = seg.get("grade") or TONE_GRADE.get(seg.get("tone", tone), "normal")
            if k > 0 and shots[k - 1].get("role") == "hook":
                trans, s["fx"] = "flash", "punch"  # sortie du hook : retour à la couleur
            elif s.get("fx") == "punch":
                trans = rng.choice(["glitch", "flash"])
            elif s.get("character"):
                trans = rng.choice(["whip", "zoom"])
            else:
                r = rng.random()
                trans = "cut" if r < 0.6 else ("slide" if r < 0.75 else ("whip" if r < 0.9 else "zoom"))
            if trans == last_trans and trans != "cut":
                trans = "cut"
        last_trans = trans
        props_shots.append({
            "from": f(s["start"]), "dur": max(1, f(s["end"]) - f(s["start"])), "src": name,
            "motion": rng.choice(["zoom-in", "zoom-in", "zoom-out", "pan-left", "pan-right", "drift-up"]),
            "grade": grade, "trans": trans, "fx": s.get("fx"), "seed": k * 17 + 3})
        if k > 0:
            cues.append((s["start"], {"whip": "whoosh", "slide": "swoosh", "zoom": "swoosh",
                                      "glitch": "glitch", "flash": "impact" if s.get("fx") else "swoosh",
                                      "cut": None}[trans]))

    # 4) sous-titres (le 1er segment est déjà écrit en gros par le hook)
    emph = {_norm(w) for sg in script["segments"] for w in sg.get("emphasis", [])}
    groups = []
    for si, x in enumerate(tl):
        if si == 0 and hook_end:
            continue
        cur: list = []
        for w in x["words"]:
            cur.append(w)
            if w["w"][-1] in ".,!?…:;" or len(cur) >= 3 or (len(cur) == 2 and len(cur[0]["w"] + w["w"]) > 12):
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
    g_props = [{"from": f(g[0]["start"]), "to": f(g[-1]["end"]) + 2,
                "words": [{"w": w["w"], "from": f(w["start"]), "to": f(w["end"]),
                           "hl": _norm(w["w"]) in emph} for w in g]} for g in groups]

    # 5) habillage
    overlays = []
    if script.get("hook_text"):
        overlays.append({"type": "hook", "text": script["hook_text"], "from": 0, "to": f(max(hook_end, 2.4))})
    if script.get("spoiler"):
        overlays.append({"type": "spoiler", "text": str(script.get("spoiler_label", "")), "from": 0, "to": f(3.5)})
    for seg, x in zip(script["segments"], tl):
        if seg.get("overlay"):
            overlays.append({"type": "rank", "text": seg["overlay"], "from": f(x["start"]), "to": f(x["slot_end"])})
            cues.append((x["start"], "impact"))
        if seg.get("stamp"):
            at = x["start"] + (x["end"] - x["start"]) * 0.35
            overlays.append({"type": "stamp", "text": seg["stamp"], "from": f(at), "to": f(min(at + 1.6, x["slot_end"]))})
            cues.append((at, "impact"))
        if seg.get("cta"):
            to = max(x["slot_end"] + 0.4, x["start"] + 2.6)
            overlays.append({"type": "cta", "from": f(x["start"]), "to": f(to), "handle": "@the.asura8",
                             "avatar": "avatar.png"})
            cues += [(x["start"], "pop"), (x["start"] + 26 / FPS, "click")]
    if script.get("reveal_text"):
        nrev = int(script.get("reveal_segments", 2))
        start = tl[-nrev]["start"] if len(tl) >= nrev else tl[-1]["start"]
        overlays.append({"type": "reveal", "text": script["reveal_text"], "from": f(start), "to": f(total)})
        cues += [(max(0, start - 1.25), "riser"), (start, "impact")]

    part = TONE_PARTICLES.get(tone)
    props = {"durationInFrames": f(total) + 1, "shots": props_shots, "groups": g_props,
             "overlays": overlays, "particles": part[0] if part else None,
             "particleColor": part[1] if part else None, "grain": True}
    # bruitages : pas plus d'un toutes les 0,35 s
    cues = sorted([c for c in cues if c[1]], key=lambda c: c[0])
    thin, last = [], -9.0
    for t, kind in cues:
        if t - last >= 0.35 or kind in ("click", "impact", "boom"):
            thin.append((t, kind))
            last = t
    (work / "timeline.json").write_text(json.dumps(props, ensure_ascii=False))
    return props, thin, music


# ------------------------------------------------------------------ rendu + audio
def ensure_node_modules() -> None:
    if not (REMOTION / "node_modules" / "remotion").exists():
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund", "--loglevel=error"], cwd=REMOTION, check=True,
                       timeout=600)


def render_video(work: Path, out: Path) -> None:
    ensure_node_modules()
    cmd = ["npx", "remotion", "render", "src/index.tsx", "AnimeShort", str(out),
           f"--props={work / 'timeline.json'}", f"--public-dir={work / 'pub'}",
           "--muted", "--codec=h264", "--crf=21", "--concurrency=2", "--log=error",
           f"--timeout=120000"]
    if Path(CHROME).exists():
        cmd.append(f"--browser-executable={CHROME}")
    subprocess.run(cmd, cwd=REMOTION, check=True, timeout=int(os.environ.get("TF_REMOTION_TIMEOUT", "900")))


def mix(voice_path: Path, music: dict, total: float, cues: list, work: Path) -> Path:
    bank = SFX.make_all(work / "sfx")
    vol = {"boom": 0.9, "impact": 0.55, "whoosh": 0.45, "swoosh": 0.35, "glitch": 0.35,
           "riser": 0.45, "click": 0.8, "pop": 0.6}
    inputs = ["-i", str(voice_path), "-ss", f"{music['offset']:.2f}", "-stream_loop", "-1",
              "-i", str(ROOT / "music" / music["file"])]
    filt = [f"[1:a]atrim=0:{total + 0.3:.2f},asetpts=PTS-STARTPTS,volume=0.2,"
            f"afade=t=in:d=0.3,afade=t=out:st={max(total - 1.5, 0):.2f}:d=1.5[m]",
            "[m][0:a]sidechaincompress=threshold=0.035:ratio=7:attack=12:release=300[duck]"]
    mix_in, n = "[0:a][duck]", 2
    for i, (t, kind) in enumerate(cues):
        inputs += ["-i", str(bank[kind])]
        lead = 0.2 if kind in ("whoosh", "swoosh") else (1.25 if kind == "riser" else 0.0)
        ms = int(max(t - lead, 0) * 1000) if kind != "riser" else int(max(t, 0) * 1000)
        filt.append(f"[{n}:a]volume={vol.get(kind, 0.5)},adelay={ms}|{ms}[s{i}]")
        mix_in += f"[s{i}]"
        n += 1
    filt.append(f"{mix_in}amix=inputs={n}:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    out = work / "mix.m4a"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", str(out)], check=True)
    return out


def render(script: dict, voice: dict, index: dict, work: Path, out_path: Path, seed: int = 0) -> dict:
    work, out_path = Path(work).resolve(), Path(out_path).resolve()
    rng = random.Random(seed)
    props, cues, music = build(script, voice, index, work, rng)
    silent = work / "video_silent.mp4"
    render_video(work, silent)
    audio = mix(Path(voice["path"]), music, voice["duration"], cues, work)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(audio), "-map", "0:v",
                    "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "5M",
                    "-bufsize", "10M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
                    "-movflags", "+faststart", str(out_path)], check=True)
    sources = sorted({s for e in index.values() for s in e.get("sources", [])})
    return {"path": str(out_path), "duration": voice["duration"], "shots": len(props["shots"]),
            "sources": sources, "music": {k: music[k] for k in ("file", "bpm", "offset")},
            "sfx": len(cues), "engine": "remotion (OpenMontage)"}
