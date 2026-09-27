"""Montage vertical 1080x1920 : plans calés sur la parole, hook visuel, sous-titres mot
par mot, appel à l'abonnement, barre de progression, musique, bruitages.

- Les changements d'image tombent sur le mot prononcé : un personnage cité apparaît
  à l'instant où son nom est dit (détection automatique + champ "at" du script).
- Motion design généré par code (lignes de vitesse façon manga, flash, zoom punch,
  tremblement) : aucune image générée par IA, aucun personnage redessiné.
"""
from __future__ import annotations

import math
import random
import re
import subprocess
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageStat

from . import assets as A

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
OVER = 1.14  # marge pour les mouvements de caméra
MUSIC = {"pote": "pote.mp3", "conteur": "mystere.mp3", "hype": "hype.mp3",
         "hype2": "hype2.mp3", "pose": "triste.mp3", "triste": "triste.mp3",
         "mystere": "mystere.mp3"}
YELLOW = "&H0000D4FF&"  # BGR ASS
WHITE = "&H00FFFFFF&"
MIN_SHOT, MAX_SHOT = 0.8, 3.0


def run(cmd: list[str], **kw) -> None:
    subprocess.run(cmd, check=True, **kw)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if c.isalnum())


# ------------------------------------------------------------------ motion design
def _speedlines(size: tuple[int, int], color: tuple[int, int, int], rng: random.Random) -> Image.Image:
    """Fond 'lignes de concentration' façon manga, teinté avec la couleur de l'image."""
    w, h = size
    base = tuple(int(c * 0.35) for c in color)
    im = Image.new("RGB", size, base)
    d = ImageDraw.Draw(im)
    cx, cy = w / 2, h * 0.42
    R = math.hypot(w, h)
    light = tuple(min(255, int(c * 0.6 + 110)) for c in color)
    for _ in range(170):
        a = rng.uniform(0, 2 * math.pi)
        spread = rng.uniform(0.004, 0.018)
        r0 = rng.uniform(0.18, 0.42) * min(w, h)
        pts = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
               (cx + R * math.cos(a - spread), cy + R * math.sin(a - spread)),
               (cx + R * math.cos(a + spread), cy + R * math.sin(a + spread))]
        d.polygon(pts, fill=light if rng.random() < 0.7 else (255, 255, 255))
    # vignette
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse([-w * 0.3, -h * 0.15, w * 1.3, h * 1.15], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(im, Image.new("RGB", size, (0, 0, 0)), mask)


def _dominant(im: Image.Image) -> tuple[int, int, int]:
    small = im.resize((40, 40)).convert("RGB")
    r, g, b = ImageStat.Stat(small).mean
    mx = max(r, g, b, 1)
    # couleur saturée
    return tuple(int(min(255, c / mx * 220)) for c in (r, g, b))


def _compose_still(img_path: str, out: Path, rng: random.Random, style: str = "auto") -> None:
    """Image 9:16 surdimensionnée : plein cadre si possible, sinon carte sur fond
    (flou de l'image ou lignes de vitesse)."""
    cw, ch = int(W * OVER), int(H * OVER)
    im = ImageOps.exif_transpose(Image.open(img_path)).convert("RGB")
    ratio = im.width / im.height
    tall_enough = 0.5 <= ratio <= 0.8 and im.height >= 900
    if tall_enough and style != "lines":
        ImageOps.fit(im, (cw, ch), Image.LANCZOS).save(out, quality=92)
        return
    small_portrait = ratio <= 1 and im.height < 900
    use_lines = style == "lines" or (style == "auto" and (small_portrait or rng.random() < 0.35))
    if use_lines:
        canvas = _speedlines((cw, ch), _dominant(im), rng)
    else:
        canvas = ImageOps.fit(im, (cw, ch), Image.LANCZOS).filter(ImageFilter.GaussianBlur(38))
        canvas = Image.eval(canvas, lambda v: int(v * 0.55))
    if ratio > 1:  # capture / bannière : grande et recadrée
        fh = int(ch * (0.46 if ratio < 2.2 else 0.34))
        fg = im.resize((int(fh * ratio), fh), Image.LANCZOS)
        maxw = int(cw * 0.96)
        if fg.width > maxw:
            off = (fg.width - maxw) // 2
            fg = fg.crop((off, 0, off + maxw, fh))
    else:  # portrait (fiche perso, affiche)
        fh = int(ch * (0.62 if small_portrait else 0.7))
        fg = im.resize((int(fh * ratio), fh), Image.LANCZOS)
    mask = Image.new("L", fg.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *fg.size], radius=34, fill=255)
    x, y = (cw - fg.width) // 2, int((ch - fg.height) * 0.40)
    # liseré blanc + ombre
    border = Image.new("L", (fg.width + 16, fg.height + 16), 0)
    ImageDraw.Draw(border).rounded_rectangle([0, 0, fg.width + 15, fg.height + 15], radius=40, fill=255)
    shadow = border.resize((fg.width + 60, fg.height + 60)).filter(ImageFilter.GaussianBlur(24))
    canvas.paste(Image.new("RGB", shadow.size, (0, 0, 0)), (x - 30, y - 18), shadow)
    canvas.paste(Image.new("RGB", border.size, (255, 255, 255)), (x - 8, y - 8), border)
    canvas.paste(fg, (x, y), mask)
    canvas.save(out, quality=92)


def _vf(d: float, fx: str, rng: random.Random) -> str:
    """Filtre caméra. fx : hook (zoom punch fort + tremblement + flash), punch (léger),
    sinon mouvement lent aléatoire."""
    if fx in ("hook", "punch"):
        amp, tp, shake, flash = (0.40, 0.32, 22, 0.22) if fx == "hook" else (0.18, 0.2, 10, 0.12)
        push = rng.uniform(0.05, 0.09)
        return (f"scale=w='trunc({W}*(1.08+{amp}*pow(max(0,1-t/{tp}),2)+{push}*t/{d:.3f})/2)*2':"
                f"h=-2:eval=frame:flags=bicubic,"
                f"crop={W}:{H}:x='(iw-ow)/2+{shake}*sin(t*67)*max(0,1-t/0.45)':"
                f"y='(ih-oh)/2+{shake}*cos(t*53)*max(0,1-t/0.45)',"
                f"fade=t=in:st=0:d={flash}:color=white")
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


def _shot_clip(still: Path, d: float, out: Path, fx: str, rng: random.Random) -> None:
    frames = max(1, round(d * FPS))
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(still),
         "-vf", _vf(frames / FPS, fx, rng) + ",format=yuv420p,setsar=1", "-frames:v", str(frames),
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(out)])


# ------------------------------------------------------------------ plan des plans
def _char_tokens(index: dict) -> list[tuple[str, str, str]]:
    """(token normalisé, anime, nom complet) pour chaque personnage connu."""
    toks = []
    for anime, e in index.items():
        for name in e.get("characters", {}):
            for part in re.split(r"[\s,]+", name):
                n = _norm(part)
                if len(n) >= 4:
                    toks.append((n, anime, name))
                    if n.endswith("ou") and len(n) >= 5:  # Gojou -> Gojo
                        toks.append((n[:-1], anime, name))
    return toks


def plan_shots(script: dict, timeline: list[dict], index: dict, rng: random.Random) -> list[dict]:
    main = script["animes"][0]
    toks = _char_tokens(index)
    cues: list[dict] = []
    for seg, tl in zip(script["segments"], timeline):
        words = tl["words"]
        seg_anime = (seg.get("shots") or [{}])[0].get("anime", main)
        explicit = seg.get("shots") or []
        for k, sh in enumerate(explicit):
            t = tl["start"] if k == 0 else tl["start"] + (tl["end"] - tl["start"]) * k / len(explicit)
            if sh.get("at"):
                target = _norm(sh["at"].split()[0])
                for w in words:
                    if target and _norm(w["w"]).startswith(target):
                        t = w["start"]
                        break
            cues.append({"t": max(0.0, t - 0.04), "prio": 3, "anime": sh.get("anime", seg_anime),
                         "kind": sh.get("kind", "any"), "character": sh.get("character"),
                         "fx": "punch" if (seg.get("sfx") and k == 0) else None})
        # personnages cités dans le texte -> image au moment où le nom est dit
        for w in words:
            nw = _norm(w["w"])
            if len(nw) < 4:
                continue
            for tok, anime, name in toks:
                if nw == tok or (len(nw) >= 5 and (nw.startswith(tok) or tok.startswith(nw))):
                    cues.append({"t": max(0.0, w["start"] - 0.04), "prio": 2, "anime": anime,
                                 "kind": "character", "character": name, "fx": None})
                    break
        if not explicit:
            cues.append({"t": tl["start"], "prio": 1, "anime": seg_anime, "kind": "any",
                         "character": None, "fx": "punch" if seg.get("sfx") else None})
    # tri + fusion des repères trop proches (le plus prioritaire gagne)
    cues.sort(key=lambda c: (c["t"], -c["prio"]))
    merged: list[dict] = []
    for c in cues:
        if merged and c["t"] - merged[-1]["t"] < MIN_SHOT:
            if c["prio"] > merged[-1]["prio"] or (c["prio"] == merged[-1]["prio"] == 2 and
                                                  c["character"] != merged[-1]["character"]):
                # l'image du perso tombe sur son nom : le plan précédent s'allonge
                merged[-1] = {**c, "fx": merged[-1]["fx"] or c["fx"]}
            continue
        merged.append(dict(c))
    if not merged or merged[0]["t"] > 0:
        merged.insert(0, {"t": 0.0, "prio": 1, "anime": main, "kind": "any", "character": None, "fx": None})
    merged[0]["t"], merged[0]["fx"] = 0.0, "hook"
    total = timeline[-1]["slot_end"]
    # combler les trous trop longs avec des images du même anime
    shots: list[dict] = []
    for i, c in enumerate(merged):
        end = merged[i + 1]["t"] if i + 1 < len(merged) else total
        dur = end - c["t"]
        n = max(1, math.ceil(dur / rng.uniform(2.3, MAX_SHOT)))
        for j in range(n):
            s = c["t"] + dur * j / n
            shots.append({**(c if j == 0 else {"anime": c["anime"], "kind": "any", "character": None,
                                               "fx": None}),
                          "start": s, "end": c["t"] + dur * (j + 1) / n})
    return shots


# ------------------------------------------------------------------ sous-titres
def _ass_time(t: float) -> str:
    t = max(t, 0)
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def _groups(words: list[dict]) -> list[list[dict]]:
    """Groupes de 1 à 3 mots, coupure après la ponctuation."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        txt = "".join(x["w"] for x in cur)
        if re.search(r"[.,!?…:;]$", w["w"]) or len(cur) >= 3 or (len(cur) == 2 and len(txt) > 13):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def build_ass(script: dict, timeline: list[dict], out: Path) -> None:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Anton,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,8,3,5,60,60,0
Style: Hook,Anton,118,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,10,6,8,60,60,230
Style: Tag,Anton,54,&H00FFFFFF,&H00FFFFFF,&H000000C8,&H000000C8,0,0,0,0,100,100,2,0,3,14,0,8,70,70,120
Style: Rank,Anton,230,&H0000D4FF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,10,4,7,70,70,210
Style: Reveal,Anton,150,&H0000D4FF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,9,4,5,60,60,0
Style: Cta,Anton,76,&H00FFFFFF,&H00FFFFFF,&H001E1EFF,&H001E1EFF,0,0,0,0,100,100,2,0,3,22,0,5,60,60,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    emph = {_norm(w) for s in script["segments"] for w in s.get("emphasis", [])}
    hook_end = max(timeline[0]["slot_end"], 2.6)
    has_hook = bool(script.get("hook_text"))
    for si, (seg, tl) in enumerate(zip(script["segments"], timeline)):
        for g in ([] if (si == 0 and has_hook) else _groups(tl["words"])):
            t0, t1 = g[0]["start"], g[-1]["end"]
            parts = []
            for w in g:
                col = YELLOW if _norm(w["w"]) in emph else WHITE
                parts.append(f"{{\\c{col}}}{_esc(w['w'])}")
            y = 1330
            ev.append(f"Dialogue: 2,{_ass_time(t0)},{_ass_time(t1)},Sub,,0,0,0,,"
                      f"{{\\pos({W//2},{y})\\fscx78\\fscy78\\t(0,80,\\fscx104\\fscy104)\\t(80,140,\\fscx100\\fscy100)}}"
                      + " ".join(parts))
        if seg.get("overlay"):
            ev.append(f"Dialogue: 3,{_ass_time(tl['start'])},{_ass_time(tl['slot_end'])},Rank,,0,0,0,,"
                      f"{{\\fscx40\\fscy40\\t(0,120,\\fscx110\\fscy110)\\t(120,200,\\fscx100\\fscy100)}}"
                      f"{_esc(seg['overlay'])}")
        if seg.get("cta"):
            t0 = tl["start"]
            ev.append(f"Dialogue: 5,{_ass_time(t0)},{_ass_time(tl['slot_end'] + 0.3)},Cta,,0,0,0,,"
                      f"{{\\pos({W//2},1640)\\fscx30\\fscy30\\t(0,140,\\fscx112\\fscy112)"
                      f"\\t(140,240,\\fscx100\\fscy100)\\t(900,1000,\\frz-4)\\t(1000,1100,\\frz4)"
                      f"\\t(1100,1200,\\frz0)}}+ ABONNE-TOI")
    # hook : les mots claquent un par un, dernier mot en jaune
    hook_words = _esc(script.get("hook_text", "")).upper().split()
    if hook_words:
        parts = []
        step = min(110, int(1400 / max(len(hook_words), 1)))
        for i, w in enumerate(hook_words):
            col = YELLOW if i == len(hook_words) - 1 or _norm(w) in emph else WHITE
            t = 80 + i * step
            parts.append(f"{{\\alpha&HFF&\\c{col}\\t({t},{t + 40},\\alpha&H00&)}}{w}")
        ev.append(f"Dialogue: 6,{_ass_time(0)},{_ass_time(hook_end)},Hook,,0,0,0,,"
                  f"{{\\fscx120\\fscy120\\t(0,200,\\fscx100\\fscy100)}}" + " ".join(parts))
    if script.get("spoiler"):
        ev.append(f"Dialogue: 7,{_ass_time(0)},{_ass_time(3.5)},Tag,,0,0,0,,"
                  f"SPOIL {_esc(str(script.get('spoiler_label', ''))).upper()}")
    if script.get("reveal_text"):
        n = int(script.get("reveal_segments", 2))
        start = timeline[-n]["start"] if len(timeline) >= n else timeline[-1]["start"]
        ev.append(f"Dialogue: 4,{_ass_time(start)},{_ass_time(timeline[-1]['slot_end'])},Reveal,,0,0,0,,"
                  f"{{\\pos({W//2},560)\\fscx50\\fscy50\\t(0,160,\\fscx110\\fscy110)\\t(160,260,\\fscx100\\fscy100)}}"
                  f"{_esc(script['reveal_text']).upper()}")
    out.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ audio
def _sfx(workdir: Path) -> tuple[Path, Path]:
    wh, boom = workdir / "whoosh.wav", workdir / "boom.wav"
    if not wh.exists():
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.6", "-af",
             "highpass=f=300,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.25,volume=0.5",
             "-ar", "44100", "-ac", "1", str(wh)])
    if not boom.exists():
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
             "sine=f=55:d=0.7", "-f", "lavfi", "-i", "anoisesrc=d=0.25:c=brown:a=0.8",
             "-filter_complex", "[0]volume=1.6,afade=t=out:st=0.05:d=0.65[a];"
             "[1]lowpass=f=400,afade=t=out:st=0.02:d=0.23[b];[a][b]amix=inputs=2:normalize=0,volume=0.9",
             "-ar", "44100", "-ac", "1", str(boom)])
    return wh, boom


def mix_audio(voice: Path, music_key: str, duration: float, sfx: list[tuple[float, str]],
              workdir: Path) -> Path:
    music = ROOT / "music" / MUSIC.get(music_key, "pote.mp3")
    wh, boom = _sfx(workdir)
    out = workdir / "mix.m4a"
    inputs = ["-i", str(voice), "-stream_loop", "-1", "-i", str(music)]
    filters = [f"[1:a]atrim=0:{duration+0.5:.2f},volume=0.17,afade=t=out:st={max(duration-1.5,0):.2f}:d=1.5[m]",
               "[m][0:a]sidechaincompress=threshold=0.04:ratio=6:attack=15:release=350[duck]"]
    mix_in, n = "[0:a][duck]", 2
    for i, (t, kind) in enumerate(sfx):
        inputs += ["-i", str(boom if kind == "boom" else wh)]
        ms = int(max(t - (0.0 if kind == "boom" else 0.2), 0) * 1000)
        filters.append(f"[{n}:a]adelay={ms}|{ms}[s{i}]")
        mix_in += f"[s{i}]"
        n += 1
    filters.append(f"{mix_in}amix=inputs={n}:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", str(out)])
    return out


# ------------------------------------------------------------------ assemblage
def render(script: dict, voice: dict, index: dict, workdir: Path, out_path: Path,
           seed: int | None = None) -> dict:
    rng = random.Random(seed)
    workdir, out_path = Path(workdir).resolve(), Path(out_path).resolve()
    shots_dir = workdir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    used: list = []
    plan = plan_shots(script, voice["timeline"], index, rng)
    clips, sfx = [], [(0.0, "boom")]
    for k, sh in enumerate(plan):
        img = A.pick(index, sh.get("anime"), sh.get("kind", "any"), sh.get("character"), used)
        if not img:
            continue
        still = shots_dir / f"s{k:03d}.jpg"
        _compose_still(img, still, rng, "lines" if sh.get("fx") == "hook" else "auto")
        clip = shots_dir / f"s{k:03d}.mp4"
        _shot_clip(still, sh["end"] - sh["start"], clip, sh.get("fx") or "", rng)
        clips.append(clip)
        if sh.get("fx") == "punch":
            sfx.append((sh["start"], "whoosh"))
    for seg, tl in zip(script["segments"], voice["timeline"]):
        if seg.get("cta"):
            sfx.append((tl["start"], "whoosh"))
    lst = shots_dir / "list.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
    silent = workdir / "video_silent.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         str(silent)], cwd=shots_dir)
    ass = workdir / "subs.ass"
    build_ass(script, voice["timeline"], ass)
    audio = mix_audio(Path(voice["path"]), script.get("music", script.get("tone", "pote")),
                      voice["duration"], sfx, workdir)
    fonts_dir = str(ROOT / "fonts")
    dur = voice["duration"]
    run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(audio),
         "-f", "lavfi", "-i", f"color=c=0xFFD400:s={W}x16:r={FPS}",
         "-filter_complex", f"[0:v]subtitles='{ass}':fontsdir='{fonts_dir}'[s];"
                            f"[s][2:v]overlay=x='-W+W*t/{dur:.3f}':y=H-16:shortest=1,format=yuv420p[v]",
         "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
         "-profile:v", "high", "-maxrate", "5M", "-bufsize", "10M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
         "-movflags", "+faststart", str(out_path)])
    sources = sorted({s for e in index.values() for s in e.get("sources", [])})
    return {"path": str(out_path), "duration": dur, "shots": len(clips), "sources": sources,
            "plan": [{k: v for k, v in s.items() if k in ("start", "character", "fx")} for s in plan]}
