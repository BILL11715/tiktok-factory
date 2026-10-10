"""Montage v3 : timeline JSON -> rendu Remotion (moteur d'OpenMontage) -> mixage audio.

Python décide QUOI montrer et QUAND (plans calés sur la parole et sur le tempo de la
musique, transitions, étalonnage, habillage, bruitages). La composition Remotion
remotion/src/AnimeShort.tsx dessine tout (motion design, transitions, sous-titres).
"""
from __future__ import annotations

import json
import math
import re
import os
import random
import shutil
import subprocess
from pathlib import Path

from . import assets as A
from . import sfx as SFX
from .render import _char_tokens, _compose_still, _norm, plan_shots

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


# ------------------------------------------------------------------ montage v4 (extraits vidéo)
def _variant(im, k: int):
    """Recadrage n°k d'une image (k=0 : entière). Une image réutilisée ne revient jamais avec
    le même cadre : gros plan haut, bas, gauche, droite..."""
    if k <= 0:
        return im
    w, h = im.size
    z = 0.62 if k % 2 else 0.72
    cw, ch = int(w * z), int(h * z)
    spots = [(0.5, 0.25), (0.5, 0.75), (0.2, 0.5), (0.8, 0.5), (0.5, 0.5), (0.25, 0.3), (0.75, 0.7)]
    fx, fy = spots[(k - 1) % len(spots)]
    x = int(min(max(0, fx * w - cw / 2), w - cw))
    y = int(min(max(0, fy * h - ch / 2), h - ch))
    return im.crop((x, y, x + cw, y + ch))


def _compose_fill(src: str, dest: Path, variant: int = 0) -> None:
    """Image plein écran 1231x2188 : fond flou + image nette centrée (persos), ou recadrage
    plein cadre si l'image est déjà assez verticale."""
    from PIL import Image, ImageFilter, ImageEnhance  # type: ignore
    W2, H2 = 1231, 2188
    im = _variant(Image.open(src).convert("RGB"), variant)
    r = im.width / im.height
    bg = im.copy()
    s = max(W2 / bg.width, H2 / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - W2) // 2, (bg.height - H2) // 2, (bg.width - W2) // 2 + W2, (bg.height - H2) // 2 + H2))
    if r <= 0.62:  # déjà vertical : plein cadre
        bg.save(dest, quality=92)
        return
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.55)
    fw = W2 if r < 1.2 else int(W2 * 1.0)
    fg = im.resize((fw, int(fw / r)), Image.LANCZOS)
    if fg.height > H2 * 0.86:
        fh = int(H2 * 0.86)
        fg = im.resize((int(fh * r), fh), Image.LANCZOS)
    bg.paste(fg, ((W2 - fg.width) // 2, int((H2 - fg.height) * 0.42)))
    bg.save(dest, quality=92)


def plan_v4(script: dict, tl: list, index: dict, clips: dict, rng: random.Random) -> list[dict]:
    """Plans calés sur les mots RÉELS : une coupe toutes les 0,8 à 1,5 s sur un début de mot,
    et l'image du personnage exactement quand son nom est prononcé."""
    main = script["animes"][0]
    toks = _char_tokens(index)
    words = []
    for si, (seg, x) in enumerate(zip(script["segments"], tl)):
        anime = (seg.get("shots") or [{}])[0].get("anime", main)
        forced = {_norm(sh["at"].split()[0]): sh for sh in seg.get("shots") or [] if sh.get("at")}
        opener = next((sh for sh in seg.get("shots") or [] if not sh.get("at") and sh.get("kind") not in (None, "any", "clip")), None)
        for wi, w in enumerate(x["words"]):
            nw = _norm(re.sub(r"^(d|l|qu|j|n|s|t|m|c)['’]", "", w["w"], flags=re.I))  # d'Aoi -> aoi
            cue = None
            if wi == 0 and opener is not None and si > 0:
                cue = {"anime": opener.get("anime", anime), "kind": opener["kind"], "character": opener.get("character")}
            elif nw and nw in forced:
                sh = forced.pop(nw)
                cue = {"anime": sh.get("anime", anime), "kind": sh.get("kind", "any"), "character": sh.get("character")}
            elif len(nw) >= 3:
                for tok, an, name in toks:
                    if nw == tok or (len(nw) >= 5 and len(tok) >= 4 and (nw.startswith(tok) or tok.startswith(nw))):
                        cue = {"anime": an, "kind": "character", "character": name}
                        break
            words.append({"t": w["start"], "seg": si, "first": wi == 0, "anime": anime, "cue": cue,
                          "sfx": bool(seg.get("sfx")) and wi == 0})
    total = tl[-1]["slot_end"]
    hook_end = tl[0]["slot_end"] if script.get("hook_text") else 0.0
    # Peu de visuels différents = plans plus longs, pour ne pas tourner en boucle.
    # Objectif : chaque extrait/image n'apparaît qu'une fois (au pire deux, recadré).
    n_media = sum(len(v) for v in clips.values()) + sum(
        len(e.get("wide", [])) + len(e.get("tall", [])) for e in index.values())
    pace = min(2.6, max(1.0, (total - hook_end) / max(1, n_media) * 1.1))
    lo, hi = pace * 0.8, pace * 1.35
    shots: list[dict] = []
    last_t, target = -9.0, 0.0
    for w in words:
        t = max(0.0, w["t"] - 0.03)
        gap = t - last_t
        in_hook = t < hook_end
        if w["cue"] is not None and shots and gap < 0.45 and not shots[-1].get("character") \
                and shots[-1].get("role") != "hook":
            # nom prononcé juste après une coupe : ce plan devient celui du personnage, et il
            # commence sur le nom (le plan d'avant s'allonge un peu)
            if len(shots) >= 2 and t - shots[-2]["start"] >= 0.5:
                shots[-2]["end"] = t
                shots[-1]["start"] = t
                last_t = t
            shots[-1].update({"anime": w["cue"]["anime"], "kind": w["cue"]["kind"],
                              "character": w["cue"].get("character")})
            target = rng.uniform(1.4, 2.0)
            continue
        want = w["cue"] is not None and gap >= 0.45
        want = want or (w["first"] and w["sfx"] and gap >= 0.45)
        want = want or gap >= target
        if not shots or want:
            if shots:
                shots[-1]["end"] = t
            c = w["cue"] or {}
            shots.append({"start": 0.0 if not shots else t, "end": total, "anime": c.get("anime", w["anime"]),
                          "kind": c.get("kind", "clip"), "character": c.get("character"),
                          "fx": "hook" if not shots else ("punch" if w["sfx"] else None),
                          "role": "hook" if in_hook else None, "seg": w["seg"]})
            last_t = t
            target = rng.uniform(0.45, 0.7) if in_hook else (rng.uniform(1.4, 2.0) if c.get("character")
                                                             else rng.uniform(lo, hi))
    shots[-1]["end"] = total
    return shots


class _Story:
    """Distribue les extraits comme une histoire, pas comme une playlist en boucle :
    - chaque segment du script = un « chapitre » tiré d'une seule source (un opening, un
      extrait sakuga), dont les plans défilent dans leur ordre d'origine (continuité) ;
    - les sources tournent d'un chapitre à l'autre ; les extraits d'action (sakuga) sont
      gardés pour la montée (2e moitié, révélations) ;
    - un extrait ne revient qu'une fois tout le stock passé, et alors en miroir, sur une
      autre portion et avec un autre mouvement de caméra."""

    def __init__(self, clips: dict, rng: random.Random):
        self.rng = rng
        self.by_anime: dict = {}
        for a, v in clips.items():
            groups: dict = {}
            for c in v:
                groups.setdefault(c.get("tag", "x"), []).append(c)
            for g in groups.values():
                g.sort(key=lambda c: (c.get("order", 0), c["path"]))
            self.by_anime[a] = groups
        self.uses: dict = {}
        self.chapter: dict = {}
        self.last_tag: dict = {}
        self.last_clip = None

    def _tags(self, anime):
        return self.by_anime.get(anime) or next((g for g in self.by_anime.values() if g), {})

    def exhausted(self, anime: str) -> bool:
        groups = self._tags(anime)
        return bool(groups) and all(self.uses.get(c["path"], 0) > 0 for g in groups.values() for c in g)

    def pick(self, anime: str, seg: int, late: bool, punch: bool):
        groups = self._tags(anime)
        if not groups:
            return None, 0
        key = (anime, seg)
        rnd = lambda c: self.uses.get(c["path"], 0)
        def fresh(tag):
            return [c for c in groups[tag] if rnd(c) == min(rnd(x) for x in groups[tag])]
        tag = self.chapter.get(key)
        if tag is None or not fresh(tag) or punch:
            low = min(rnd(c) for g in groups.values() for c in g)
            cands = [t for t, g in groups.items() if any(rnd(c) == low for c in g)]
            if len(cands) > 1 and self.last_tag.get(anime) in cands:
                cands.remove(self.last_tag[anime])
            high = [t for t in cands if groups[t][0].get("energy") == "high"]
            mid = [t for t in cands if t not in high]
            pool = (high or mid) if (late or punch) else (mid or high)
            tag = self.rng.choice(pool)
            if not punch:
                self.chapter[key] = tag
        self.last_tag[anime] = tag
        low = min(rnd(c) for c in groups[tag])
        options = [c for c in groups[tag] if rnd(c) == low and c is not self.last_clip] or groups[tag]
        c = options[0]  # ordre d'origine dans la source
        n = rnd(c)
        self.uses[c["path"]] = n + 1
        self.last_clip = c
        return c, n


def assign_media(shots: list[dict], index: dict, clips: dict, pub: Path, rng: random.Random) -> list[dict]:
    """Associe un extrait vidéo (ou une image) à chaque plan. Aucun plan ne revient à
    l'identique : extrait déjà vu = miroir + autre portion, image déjà vue = autre cadrage."""
    (pub / "clips").mkdir(exist_ok=True)
    story = _Story(clips, rng)
    total = shots[-1]["end"] if shots else 1.0
    img_uses: dict = {}
    used_imgs: list = []
    out = []

    def still(k, s, img):
        v = img_uses.get(img, 0)
        img_uses[img] = v + 1
        name = f"img/s{k:03d}.jpg"
        _compose_fill(img, pub / name, variant=v)
        return {**s, "src": name, "flip": v % 2 == 1 and not s.get("character")}

    k = 0
    while k < len(shots):
        s = shots[k]
        dur = s["end"] - s["start"]
        if s.get("character") or s.get("kind") in ("character", "poster", "wide"):
            img = A.pick(index, s["anime"], s.get("kind") if s.get("kind") != "clip" else "any",
                         s.get("character"), used_imgs)
            if img:
                out.append(still(k, s, img))
                k += 1
                continue
        late = s["start"] > total * 0.55
        if story.exhausted(s["anime"]):
            # tous les extraits déjà vus : d'abord les images jamais montrées (vignettes d'épisodes)
            e = index.get(s["anime"]) or next(iter(index.values()), {})
            fresh_img = next((p for p in e.get("wide", []) + e.get("tall", []) if p not in img_uses), None)
            if fresh_img:
                out.append(still(k, s, fresh_img))
                k += 1
                continue
        c, n = story.pick(s["anime"], s.get("seg", 0), late, s.get("fx") == "punch")
        if c is not None:
            dst = pub / "clips" / Path(c["path"]).name
            if not dst.exists():
                shutil.copy(c["path"], dst)
            room = max(0.0, c["dur"] - dur - 0.1)
            if c["dur"] + 0.05 < dur and dur > 1.6:  # extrait trop court : on coupe le plan en deux
                mid = s["start"] + c["dur"]
                out.append({**s, "end": mid, "video": f"clips/{dst.name}", "vstart": 0.0, "flip": n % 2 == 1})
                shots.insert(k + 1, {**s, "start": mid, "fx": None, "role": s.get("role")})
                k += 1
                continue
            # 1er passage : début de l'extrait (continuité) ; passages suivants : autre portion
            vstart = 0.0 if n == 0 else room * (1.0 if n % 2 else 0.5)
            out.append({**s, "video": f"clips/{dst.name}", "vstart": max(0.0, vstart), "flip": n % 2 == 1,
                        "reuse": n})
            k += 1
            continue
        img = A.pick(index, s["anime"], "wide", None, used_imgs) or A.pick(index, s["anime"], "any", None, used_imgs)
        if img:
            out.append(still(k, s, img))
        k += 1
    return out


def _dress(script: dict, tl: list, hook_end: float, total: float, tone: str, cues: list, props_shots: list,
           max_words: int = 3) -> tuple[dict, list]:
    """Sous-titres, habillage (hook, rang, tampon, abonnement, révélation), particules, bruitages."""
    # 4) sous-titres (le 1er segment est déjà écrit en gros par le hook)
    emph = {_norm(w) for sg in script["segments"] for w in sg.get("emphasis", [])}
    groups = []
    for si, x in enumerate(tl):
        if si == 0 and hook_end:
            continue
        cur: list = []
        for w in x["words"]:
            cur.append(w)
            if w["w"][-1] in ".,!?…:;" or len(cur) >= max_words or (len(cur) == 2 and len(cur[0]["w"] + w["w"]) > 12):
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
    return props, thin


def build_v4(script: dict, voice: dict, index: dict, clips: dict, work: Path, pub: Path, music: dict,
             rng: random.Random) -> tuple[dict, list, dict]:
    tl = voice["timeline"]
    total = tl[-1]["slot_end"]
    tone = script.get("tone", "pote")
    hook_end = tl[0]["slot_end"] if script.get("hook_text") else 0.0
    shots = assign_media(plan_v4(script, tl, index, clips, rng), index, clips, pub, rng)
    props_shots, cues = [], [(0.0, "boom")]
    for k, s in enumerate(shots):
        seg = script["segments"][min(s.get("seg", 0), len(script["segments"]) - 1)]
        if s.get("role") == "hook":
            grade, trans = "bw", ("cut" if k == 0 else rng.choice(["flash", "cut", "glitch"]))
        else:
            grade = seg.get("grade") or ("bw" if seg.get("tone") == "pose" else "normal")
            if k > 0 and shots[k - 1].get("role") == "hook":
                trans, s["fx"] = "flash", "punch"
            elif s.get("fx") == "punch":
                trans = rng.choice(["flash", "glitch", "zoom"])
            elif s.get("character"):
                trans = rng.choice(["cut", "zoom"])
            else:
                trans = "cut" if rng.random() < 0.85 else "whip"
        item = {"from": f(s["start"]), "dur": max(1, f(s["end"]) - f(s["start"])), "src": s.get("src", ""),
                "motion": (rng.choice(["zoom-in", "zoom-out", "pan-left", "pan-right", "drift-up"])
                           if not s.get("video") else
                           ("zoom-in" if not s.get("reuse") else rng.choice(["zoom-out", "pan-left", "pan-right"]))),
                "flip": bool(s.get("flip")),
                "grade": grade, "trans": trans, "fx": s.get("fx"), "seed": k * 17 + 3}
        if s.get("video"):
            item["video"], item["videoStart"] = s["video"], f(s.get("vstart", 0.0))
        props_shots.append(item)
        if k > 0 and trans != "cut":
            cues.append((s["start"], {"whip": "whoosh", "zoom": "swoosh", "glitch": "glitch",
                                      "flash": "impact" if s.get("fx") else "swoosh"}.get(trans)))
    props, thin = _dress(script, tl, hook_end, total, tone, cues, props_shots, max_words=2)
    if any(clips.values()):
        props["particles"] = None  # extraits vidéo : pas de particules par-dessus
    (work / "timeline.json").write_text(json.dumps(props, ensure_ascii=False))
    return props, thin, music


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

    clips = json.loads((work / "clips.json").read_text()) if (work / "clips.json").exists() else {}
    # même moteur avec ou sans extraits : sans extraits, les images (vignettes d'épisodes,
    # affiches, persos) sont recadrées et retournées pour ne jamais repasser à l'identique
    return build_v4(script, voice, index, clips, work, pub, music, rng)
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

    props, thin = _dress(script, tl, hook_end, total, tone, cues, props_shots, max_words=3)
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
           "--muted", "--codec=h264", "--crf=21", f"--concurrency={min(2, os.cpu_count() or 1)}", "--log=error",
           f"--timeout=120000", "--offthreadvideo-cache-size-in-bytes=400000000"]
    if Path(CHROME).exists():
        cmd.append(f"--browser-executable={CHROME}")
    subprocess.run(cmd, cwd=REMOTION, check=True, timeout=int(os.environ.get("TF_REMOTION_TIMEOUT", "2100")))


def mix(voice_path: Path, music: dict, total: float, cues: list, work: Path, hook_end: float = 3.0) -> Path:
    """La voix d'abord : voix normalisée et compressée, musique très basse (environ -22 dB sous la
    voix) et encore plus basse pendant le hook, coupée net dès que la voix parle (ducking),
    bruitages discrets."""
    bank = SFX.make_all(work / "sfx")
    vol = {"boom": 0.35, "impact": 0.22, "whoosh": 0.16, "swoosh": 0.12, "glitch": 0.12,
           "riser": 0.18, "click": 0.3, "pop": 0.22}
    inputs = ["-i", str(voice_path), "-ss", f"{music['offset']:.2f}", "-stream_loop", "-1",
              "-i", str(ROOT / "music" / music["file"])]
    he = max(1.0, hook_end)
    filt = [
        # voix : niveau constant, présence (léger boost 2-5 kHz), compression douce
        "[0:a]highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=3,"
        "acompressor=threshold=0.12:ratio=3:attack=5:release=120:makeup=2,"
        "loudnorm=I=-15:TP=-2:LRA=7,asplit=2[v][vkey]",
        # musique : même base de loudness puis -22 dB, -28 dB pendant le hook
        f"[1:a]atrim=0:{total + 0.3:.2f},asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-3,"
        f"volume='if(lt(t,{he:.2f}),0.06,0.13)':eval=frame,"
        f"afade=t=in:d=0.4,afade=t=out:st={max(total - 1.5, 0):.2f}:d=1.5[m]",
        "[m][vkey]sidechaincompress=threshold=0.02:ratio=12:attack=8:release=350:makeup=1[duck]",
    ]
    mix_in, n = "[v][duck]", 2
    for i, (t, kind) in enumerate(cues):
        inputs += ["-i", str(bank[kind])]
        lead = 0.2 if kind in ("whoosh", "swoosh") else (1.25 if kind == "riser" else 0.0)
        ms = int(max(t - lead, 0) * 1000) if kind != "riser" else int(max(t, 0) * 1000)
        filt.append(f"[{n}:a]volume={vol.get(kind, 0.2)},adelay={ms}|{ms}[s{i}]")
        mix_in += f"[s{i}]"
        n += 1
    # somme sans renormalisation dynamique (qui remonterait la musique dans les silences)
    filt.append(f"{mix_in}amix=inputs={n}:duration=first:normalize=0,alimiter=limit=0.89:level=false[a]")
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
    hook_end = voice["timeline"][0]["slot_end"] if script.get("hook_text") else 2.5
    audio = mix(Path(voice["path"]), music, voice["duration"], cues, work, hook_end)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(audio), "-map", "0:v",
                    "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "5M",
                    "-bufsize", "10M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
                    "-movflags", "+faststart", str(out_path)], check=True)
    sources = sorted({s for e in index.values() for s in e.get("sources", [])})
    return {"path": str(out_path), "duration": voice["duration"], "shots": len(props["shots"]),
            "sources": sources, "music": {k: music[k] for k in ("file", "bpm", "offset")},
            "sfx": len(cues), "engine": "remotion (OpenMontage)"}
