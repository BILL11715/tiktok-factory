"""Extraits vidéo animés pour le montage (plein écran, comme les gros comptes anime).

Sources automatiques, sans intervention :
  1. AnimeThemes (api.animethemes.moe / v.animethemes.moe) : openings et endings officiels,
     y compris la saison en cours, souvent sans crédits (nc).
  2. Sakugabooru (www.sakugabooru.com) : extraits d'animation notables, classés par anime.

Chaque source est découpée en plans (détection de coupes), recadrée en 9:16 (1080x1920),
muette, et rangée dans work/clips/. Si une source est injoignable, on passe à la suivante ;
sans aucun extrait, le montage retombe sur les images fixes.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "tiktok-factory/1.0 (github.com/BILL11715/tiktok-factory)"}
MAX_DL = 90 * 1024 * 1024  # 90 Mo par vidéo source
MIN_SHOT, MAX_SHOT = 0.7, 6.0


def _get_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={**UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _download(url: str, dest: Path, timeout: int = 120) -> bool:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
            n = 0
            while chunk := r.read(1 << 20):
                n += len(chunk)
                if n > MAX_DL:
                    return False
                f.write(chunk)
        return dest.stat().st_size > 100_000
    except Exception as exc:
        print(f"[clips] téléchargement impossible {url[:80]} ({exc})")
        return False


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ------------------------------------------------------------------ AnimeThemes
def animethemes_videos(name: str, anilist_id: int | None = None, limit: int = 3,
                       franchise: bool = False) -> list[dict]:
    """Openings/endings officiels. franchise=True : toutes les saisons dont le nom commence
    par `name` (saison 1, suites...), la plus récente d'abord."""
    q = urllib.parse.quote(name)
    url = (f"https://api.animethemes.moe/anime?q={q}&page[size]=10"
           f"&include=animethemes.animethemeentries.videos,resources")
    data = _get_json(url).get("anime", [])
    if not data:
        return []

    def score(a):
        ids = {(r.get("site"), str(r.get("external_id"))) for r in a.get("resources", [])}
        if anilist_id and ("AniList", str(anilist_id)) in ids:
            return 100
        return 10 if _norm(a.get("name", "")) == _norm(name) else 0

    data.sort(key=lambda a: (-score(a), -(a.get("year") or 0)))
    if franchise:
        animes = [a for a in data if _norm(a.get("name", "")).startswith(_norm(name))][:4]
    else:
        animes = data[:1]
    vids = []
    for anime in animes:
        for th in anime.get("animethemes", []):
            for en in th.get("animethemeentries", []):
                if en.get("nsfw"):
                    continue
                best = None
                for v in en.get("videos", []):
                    res = v.get("resolution") or 0
                    key = (bool(v.get("nc")), res <= 1080, res, v.get("source") == "BD")
                    if best is None or key > best[0]:
                        best = (key, v)
                if best:
                    v = best[1]
                    vids.append({"url": v["link"], "nc": bool(v.get("nc")), "res": v.get("resolution"),
                                 "label": f"{anime['name']} {th.get('slug')}", "source": "AnimeThemes",
                                 "type": th.get("type"), "year": anime.get("year") or 0})
    # sans version "nc" les crédits sont incrustés : on ne garde alors que les openings
    vids = [v for v in vids if v["nc"] or v["type"] == "OP"]
    vids.sort(key=lambda v: (-v["year"], not v["nc"], v["type"] != "OP"))
    return vids[:limit]


def base_title(name: str) -> str:
    """Nom de la franchise : 'Dandadan 3rd Season' -> 'Dandadan',
    'Tokyo Revengers: Santen Sensou-hen' -> 'Tokyo Revengers'."""
    b = re.split(r"\s*[:(]\s*", name)[0]
    b = re.sub(r"\s+(season|saison|part|cour)\s*\d+.*$", "", b, flags=re.I)
    b = re.sub(r"\s+\d+(st|nd|rd|th)\s+(season|part|cour).*$", "", b, flags=re.I)
    b = re.sub(r"\s+(ii|iii|iv|\d)$", "", b, flags=re.I)
    return b.strip()


# ------------------------------------------------------------------ Sakugabooru
def sakuga_videos(name: str, limit: int = 14) -> list[dict]:
    base = "https://www.sakugabooru.com"
    tags = _get_json(f"{base}/tag.json?name={urllib.parse.quote(re.sub(chr(32), chr(95), name.lower()))}&type=3&order=count&limit=5")
    if not tags:
        return []
    tag = tags[0]["name"]
    posts = _get_json(f"{base}/post.json?tags={urllib.parse.quote(tag)}+order:score&limit=40")
    out = []
    for p in posts:
        u = p.get("file_url", "")
        if u.endswith((".mp4", ".webm")) and p.get("rating", "s") == "s" and (p.get("file_size") or 0) < 40e6:
            out.append({"url": u, "label": f"sakuga {p.get('id')}", "source": "Sakugabooru", "nc": True})
        if len(out) >= limit:
            break
    return out


# ------------------------------------------------------------------ découpe
def _scenes(path: Path) -> list[float]:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf",
                          "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", out)]


def _dur(path: Path) -> float:
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(path)], capture_output=True, text=True).stdout.strip()
    return float(o or 0)


def _luma(path: Path, t: float) -> float:
    """Luminosité moyenne d'une image (évite les plans noirs/blancs de transition)."""
    o = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                        "-vf", "scale=32:18,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return sum(o) / max(1, len(o))


def split(src: Path, out_dir: Path, tag: str, skip_head: float, skip_tail: float, max_shots: int) -> list[dict]:
    d = _dur(src)
    cuts = [0.0] + _scenes(src) + [d]
    shots = []
    for a, b in zip(cuts, cuts[1:]):
        a2, b2 = a + 0.08, b - 0.08  # marge contre les fondus
        if a2 < skip_head or b2 > d - skip_tail or b2 - a2 < MIN_SHOT:
            continue
        mid = (a2 + b2) / 2
        if not 25 < _luma(src, mid) < 235:
            continue
        shots.append((a2, min(b2, a2 + MAX_SHOT)))
    # répartir sur toute la vidéo plutôt que prendre les premiers
    if len(shots) > max_shots:
        step = len(shots) / max_shots
        shots = [shots[int(i * step)] for i in range(max_shots)]
    res = []
    for i, (a, b) in enumerate(shots):
        out = out_dir / f"{tag}_{i:02d}.mp4"
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(src),
                            "-filter_complex", FRAME_9x16,
                            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(out)])
        if r.returncode == 0 and out.exists():
            res.append({"path": str(out), "dur": round(b - a, 3), "tag": tag})
    return res


# Cadrage 9:16 sans sur-zoom : l'extrait 16:9 garde ~2/3 de sa largeur (persos entiers),
# centré sur un fond flou et assombri du même plan (style des gros comptes anime).
FG_W = 1600
FRAME_9x16 = (
    "[0:v]split[a][b];"
    "[a]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:2,"
    "scale=1080:1920:flags=bicubic,eq=brightness=-0.14:saturation=1.1[bg];"
    f"[b]scale={FG_W}:-2:flags=lanczos,crop='min(iw,1080)':'min(ih,1920)'[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2-60,fps=30,format=yuv420p"
)


def collect(animes: list[str], work: Path, index: dict | None = None, per_anime: int = 60) -> dict:
    """Retourne {anime: [{"path","dur","tag","source"}...]} et écrit work/clips.json."""
    out_dir = work / "clips"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = work / "clips_src"
    raw.mkdir(exist_ok=True)
    result: dict = {}
    for ai, anime in enumerate(animes):
        meta = ((index or {}).get(anime) or {}).get("meta") or {}
        anilist_id = meta.get("anilist_id")
        titles = meta.get("titles") or {}
        names = [anime] + [n for n in (titles.get("en_jp"), titles.get("en"), meta.get("title"))
                           if n and _norm(n) != _norm(anime)]
        names = list(dict.fromkeys(names))
        bases = list(dict.fromkeys(b for b in (base_title(n) for n in names) if len(b) >= 5))
        sources: list[dict] = []
        seen: set = set()

        def _add(got):
            for g in got:
                if g["url"] not in seen:
                    seen.add(g["url"])
                    sources.append(g)

        # a) openings/endings de la saison demandée
        for n in names:
            try:
                got = animethemes_videos(n, anilist_id, limit=3)
            except Exception as exc:
                print(f"[clips] AnimeThemes indisponible pour {n} ({exc})")
                got = []
            if got:
                _add(got)
                break
        # b) extraits sakuga (saison puis franchise)
        for n in names + bases:
            try:
                got = sakuga_videos(n)
            except Exception as exc:
                print(f"[clips] Sakugabooru indisponible pour {n} ({exc})")
                got = []
            if got:
                _add(got)
                break
        # c) openings/endings des autres saisons de la franchise : de la matière en plus
        for b in bases:
            try:
                _add(animethemes_videos(b, None, limit=5, franchise=True))
            except Exception as exc:
                print(f"[clips] AnimeThemes (franchise) indisponible pour {b} ({exc})")
        themes = [v for v in sources if v["source"] == "AnimeThemes"][:5]
        sakus = [v for v in sources if v["source"] == "Sakugabooru"]
        # alterner les sources pour ne pas tout prendre dans un seul opening
        order: list[dict] = []
        while themes or sakus:
            if themes:
                order.append(themes.pop(0))
            for _ in range(3):
                if sakus:
                    order.append(sakus.pop(0))
        sources = order
        shots: list[dict] = []
        budget = per_anime if len(animes) == 1 else max(14, per_anime // len(animes))
        n_themes = max(1, sum(1 for v in sources if v["source"] == "AnimeThemes"))
        per_theme = max(8, min(16, budget // n_themes))
        for k, v in enumerate(sources):
            if len(shots) >= budget:
                break
            if v["source"] == "Sakugabooru" and sum(1 for x in shots if "Sakuga" in x.get("source", "")) >= budget // 2:
                continue
            ext = ".webm" if v["url"].endswith(".webm") else ".mp4"
            src = raw / f"a{ai}_{k}{ext}"
            if not _download(v["url"], src):
                continue
            is_theme = v["source"] == "AnimeThemes"
            # openings : on saute le titre et la fin (crédits, logo)
            got = split(src, out_dir, f"a{ai}_{k}", 3.0 if is_theme else 0.0, 5.0 if is_theme else 0.0,
                        min(per_theme if is_theme else 3, budget - len(shots)))
            for i, g in enumerate(got):
                g["source"] = f"{v['source']} ({v['label']})"
                g["order"] = i  # ordre chronologique dans la source (continuité du montage)
                g["energy"] = "high" if not is_theme else "mid"
            shots += got
            src.unlink(missing_ok=True)
        print(f"[clips] {anime} : {len(shots)} extraits ({', '.join(sorted({s['source'].split(' (')[0] for s in shots})) or 'aucun'})")
        result[anime] = shots
    (work / "clips.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return result
