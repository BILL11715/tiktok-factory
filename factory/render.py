"""Montage vertical 1080x1920 : plans animés, sous-titres mot par mot, musique, bruitages.

Choix "anti-IA" : coupes franches, mouvements de caméra variés et irréguliers,
sous-titres courts façon CapCut, bruitages seulement sur les révélations.
"""
from __future__ import annotations

import json
import random
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from . import assets as A

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
OVER = 1.14  # marge pour les mouvements de caméra
FONT = ROOT / "fonts" / "Anton-Regular.ttf"
MUSIC = {"pote": "pote.mp3", "conteur": "mystere.mp3", "hype": "hype.mp3",
         "hype2": "hype2.mp3", "pose": "triste.mp3", "triste": "triste.mp3",
         "mystere": "mystere.mp3"}
YELLOW = "&H0000D4FF&"  # BGR ASS
WHITE = "&H00FFFFFF&"


def run(cmd: list[str], **kw) -> None:
    subprocess.run(cmd, check=True, **kw)


# ------------------------------------------------------------------ images
def _compose_still(img_path: str, out: Path, label: str | None = None) -> None:
    """Crée une image 9:16 surdimensionnée : plein cadre si l'image s'y prête,
    sinon carte centrée sur fond flouté (personnages, bannières)."""
    cw, ch = int(W * OVER), int(H * OVER)
    im = ImageOps.exif_transpose(Image.open(img_path)).convert("RGB")
    ratio = im.width / im.height
    bg = ImageOps.fit(im, (cw, ch), Image.LANCZOS)
    tall_enough = 0.5 <= ratio <= 0.8 and im.height >= 900
    if tall_enough:
        canvas = bg
    else:
        canvas = bg.filter(ImageFilter.GaussianBlur(38))
        canvas = Image.eval(canvas, lambda v: int(v * 0.55))
        if ratio > 1:  # image large (capture, bannière) : grande et recadrée
            fh = int(ch * (0.46 if ratio < 2.2 else 0.34))
            fg = im.resize((int(fh * ratio), fh), Image.LANCZOS)
            maxw = int(cw * 0.96)
            if fg.width > maxw:
                off = (fg.width - maxw) // 2
                fg = fg.crop((off, 0, off + maxw, fh))
        else:  # portrait petit (fiche perso)
            fh = int(ch * 0.58)
            fg = im.resize((int(fh * ratio), fh), Image.LANCZOS)
        mask = Image.new("L", fg.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, *fg.size], radius=34, fill=255)
        x, y = (cw - fg.width) // 2, int((ch - fg.height) * 0.40)
        shadow = Image.new("L", (fg.width + 60, fg.height + 60), 0)
        ImageDraw.Draw(shadow).rounded_rectangle([30, 30, fg.width + 30, fg.height + 30], radius=40, fill=160)
        shadow = shadow.filter(ImageFilter.GaussianBlur(22))
        canvas.paste(Image.new("RGB", shadow.size, (0, 0, 0)), (x - 30, y - 18), shadow)
        canvas.paste(fg, (x, y), mask)
    canvas.save(out, quality=92)


def _motion(d: float, rng: random.Random) -> str:
    """Mouvement de caméra : zoom avant/arrière (scale évalué par image) ou panoramique."""
    kind = rng.choice(["in", "in", "out", "left", "right", "up"])
    if kind in ("in", "out"):
        z = rng.uniform(0.07, 0.13)
        f = f"(t/{d:.3f})" if kind == "in" else f"(1-t/{d:.3f})"
        return (f"scale=w='trunc({W}*(1.02+{z:.3f}*{f})/2)*2':h=-2:eval=frame:flags=bicubic,"
                f"crop={W}:{H}")
    if kind in ("left", "right"):
        f = f"(t/{d:.3f})" if kind == "left" else f"(1-t/{d:.3f})"
        return f"crop={W}:{H}:x='(iw-ow)*{f}':y='(ih-oh)/2'"
    return f"crop={W}:{H}:x='(iw-ow)/2':y='(ih-oh)*(1-t/{d:.3f})'"


def _shot_clip(still: Path, d: float, out: Path, rng: random.Random) -> None:
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}",
         "-i", str(still), "-vf", _motion(d, rng) + ",format=yuv420p,setsar=1",
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(out)])


# ------------------------------------------------------------------ sous-titres
def _ass_time(t: float) -> str:
    t = max(t, 0)
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _chunks(text: str) -> list[str]:
    """Découpe en groupes de 1 à 3 mots, coupure après la ponctuation."""
    words = text.split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.,!?…:;]$", w) or len(cur) >= 3 or (len(cur) == 2 and len("".join(cur)) > 13):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def _esc(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def build_ass(script: dict, timeline: list[dict], out: Path) -> None:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Anton,124,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,7,3,5,60,60,0
Style: Hook,Anton,108,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,1,0,3,18,0,8,70,70,250
Style: Tag,Anton,54,&H00FFFFFF,&H00FFFFFF,&H000000C8,&H000000C8,0,0,0,0,100,100,2,0,3,14,0,8,70,70,140
Style: Rank,Anton,230,&H0000D4FF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,10,4,7,70,70,210
Style: Reveal,Anton,150,&H0000D4FF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,9,4,5,60,60,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    emph = {w.lower().strip(".,!?…") for s in script["segments"] for w in s.get("emphasis", [])}
    y_sub = 1330
    for seg, tl in zip(script["segments"], timeline):
        chunks = _chunks(seg["text"])
        total_chars = sum(len(c) for c in chunks) or 1
        t, span = tl["start"], tl["end"] - tl["start"]
        for c in chunks:
            d = span * len(c) / total_chars
            words = []
            for w in c.split():
                key = w.lower().strip(".,!?…'\"")
                col = YELLOW if key in emph else WHITE
                words.append(f"{{\\c{col}}}{_esc(w)}")
            txt = " ".join(words)
            ev.append(f"Dialogue: 2,{_ass_time(t)},{_ass_time(t + d)},Sub,,0,0,0,,"
                      f"{{\\pos({W//2},{y_sub})\\fscx82\\fscy82\\t(0,90,\\fscx100\\fscy100)}}{txt}")
            t += d
        if seg.get("overlay"):
            ev.append(f"Dialogue: 3,{_ass_time(tl['start'])},{_ass_time(tl['slot_end'])},Rank,,0,0,0,,"
                      f"{{\\fad(80,0)}}{_esc(seg['overlay'])}")
    # hook en haut pendant le premier segment
    first = timeline[0]
    hook = _esc(script.get("hook_text", "")).upper()
    if hook:
        ev.append(f"Dialogue: 4,{_ass_time(0)},{_ass_time(max(first['slot_end'], 2.8))},Hook,,0,0,0,,{hook}")
    if script.get("spoiler"):
        ev.append(f"Dialogue: 5,{_ass_time(0)},{_ass_time(3.5)},Tag,,0,0,0,,"
                  f"{{\\c&H00FFFFFF&}}SPOIL {_esc(str(script.get('spoiler_label', ''))).upper()}")
    # révélation (nom de l'anime) sur les derniers segments
    if script.get("reveal_text"):
        n = int(script.get("reveal_segments", 2))
        start = timeline[-n]["start"] if len(timeline) >= n else timeline[-1]["start"]
        ev.append(f"Dialogue: 4,{_ass_time(start)},{_ass_time(timeline[-1]['slot_end'])},Reveal,,0,0,0,,"
                  f"{{\\pos({W//2},560)\\fscx60\\fscy60\\t(0,160,\\fscx100\\fscy100)}}"
                  f"{_esc(script['reveal_text']).upper()}")
    out.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ audio
def _whoosh(path: Path) -> None:
    if path.exists():
        return
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         "anoisesrc=d=0.45:c=pink:a=0.6", "-af",
         "highpass=f=300,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.25,volume=0.5",
         "-ar", "44100", "-ac", "1", str(path)])


def mix_audio(voice: Path, music_key: str, duration: float, sfx_times: list[float],
              workdir: Path) -> Path:
    music = ROOT / "music" / MUSIC.get(music_key, "pote.mp3")
    wh = workdir / "whoosh.wav"
    _whoosh(wh)
    out = workdir / "mix.m4a"
    inputs = ["-i", str(voice), "-stream_loop", "-1", "-i", str(music)]
    filters = [f"[1:a]atrim=0:{duration+0.5:.2f},volume=0.16,afade=t=out:st={max(duration-1.5,0):.2f}:d=1.5[m]",
               "[m][0:a]sidechaincompress=threshold=0.04:ratio=6:attack=15:release=350[duck]"]
    mix_in = "[0:a][duck]"
    n = 2
    for i, t in enumerate(sfx_times):
        inputs += ["-i", str(wh)]
        filters.append(f"[{n}:a]adelay={int(max(t-0.2,0)*1000)}|{int(max(t-0.2,0)*1000)}[s{i}]")
        mix_in += f"[s{i}]"
        n += 1
    filters.append(f"{mix_in}amix=inputs={n}:duration=first:normalize=0,"
                   f"loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", str(out)])
    return out


# ------------------------------------------------------------------ assemblage
def render(script: dict, voice: dict, index: dict, workdir: Path, out_path: Path,
           seed: int | None = None) -> dict:
    rng = random.Random(seed)
    shots_dir = workdir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    used: list = []
    clips, sfx_times, sources = [], [], set()
    main_anime = script["animes"][0]
    k = 0
    for seg, tl in zip(script["segments"], voice["timeline"]):
        slot = tl["slot_end"] - tl["start"]
        shots = seg.get("shots") or []
        n_auto = max(1, round(slot / rng.uniform(2.4, 3.6)))
        if len(shots) < n_auto:  # compléter pour garder un plan toutes les 2-4 s
            shots = shots + [{"anime": (shots[-1]["anime"] if shots else main_anime)}] * (n_auto - len(shots))
        # durées légèrement irrégulières
        weights = [rng.uniform(0.8, 1.25) for _ in shots]
        tot = sum(weights)
        t_local = tl["start"]
        for shot, w in zip(shots, weights):
            d = slot * w / tot
            img = A.pick(index, shot.get("anime", main_anime), shot.get("kind", "any"),
                         shot.get("character"), used)
            if not img:
                continue
            still = shots_dir / f"s{k:03d}.jpg"
            _compose_still(img, still)
            clip = shots_dir / f"s{k:03d}.mp4"
            _shot_clip(still, d, clip, rng)
            clips.append(clip)
            k += 1
            t_local += d
        if seg.get("sfx"):
            sfx_times.append(tl["start"])
        a = index.get(seg.get("shots", [{}])[0].get("anime", main_anime) if seg.get("shots") else main_anime)
        for s in (a or {}).get("sources", []):
            sources.add(s)
    lst = shots_dir / "list.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
    silent = workdir / "video_silent.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         str(silent)], cwd=shots_dir)
    ass = workdir / "subs.ass"
    build_ass(script, voice["timeline"], ass)
    audio = mix_audio(Path(voice["path"]), script.get("music", script.get("tone", "pote")),
                      voice["duration"], sfx_times, workdir)
    fonts_dir = str(ROOT / "fonts")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(audio),
         "-vf", f"subtitles='{ass}':fontsdir='{fonts_dir}',format=yuv420p",
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
         "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
         "-movflags", "+faststart", str(out_path)])
    return {"path": str(out_path), "duration": voice["duration"], "shots": len(clips),
            "sources": sorted(sources)}
