"""Récupération des visuels officiels (affiches, key visuals, personnages).

Sources : Kitsu (principale, stable) puis Jikan / MyAnimeList (secours).
Aucune image générée par IA, aucun extrait d'épisode.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

UA = {"User-Agent": "tiktok-factory/1.0 (+github.com/BILL11715/tiktok-factory)"}
KITSU = "https://kitsu.io/api/edge"
JIKAN = "https://api.jikan.moe/v4"


def _get(url: str, params: dict | None = None, tries: int = 3):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=20)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (i + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(1.5 * (i + 1))
    return None


def _download(url: str, dest_dir: Path) -> Path | None:
    if not url:
        return None
    ext = ".png" if url.lower().split("?")[0].endswith(".png") else ".jpg"
    path = dest_dir / (hashlib.md5(url.encode()).hexdigest()[:12] + ext)
    if path.exists():
        return path
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code == 200 and len(r.content) > 5000:
            path.write_bytes(r.content)
            return path
    except requests.RequestException:
        pass
    return None


def _norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


# --------------------------------------------------------------------- Kitsu
def kitsu_search(query: str) -> list:
    d = _get(f"{KITSU}/anime", {"filter[text]": query, "page[limit]": 12})
    return (d or {}).get("data") or []


def kitsu_anime(query: str) -> dict | None:
    d = {"data": kitsu_search(query)}
    if not d["data"]:
        return None
    # préférence : titre qui contient la requête, sinon le plus populaire
    q = _norm(query)
    items = d["data"]
    items.sort(key=lambda a: (q not in _norm(a["attributes"].get("canonicalTitle", "")),
                              a["attributes"].get("popularityRank") or 99999))
    return items[0]


def kitsu_images(query: str) -> dict:
    out = {"anime": None, "poster": [], "cover": [], "characters": {}, "episodes": []}
    a = kitsu_anime(query)
    if not a:
        return out
    at = a["attributes"]
    out["anime"] = {"id": a["id"], "title": at.get("canonicalTitle"),
                    "titles": at.get("titles"), "synopsis": at.get("synopsis"),
                    "episodes": at.get("episodeCount"), "start": at.get("startDate"),
                    "source": f"https://kitsu.io/anime/{at.get('slug')}"}
    q = _norm(query)
    main_key = _norm(at.get("canonicalTitle", ""))[:10]

    def _titles(x):
        xa = x["attributes"]
        return [_norm(t or "") for t in [xa.get("canonicalTitle"), *(xa.get("titles") or {}).values()]]

    franchise = [a] + [x for x in kitsu_search(query) if x["id"] != a["id"]
                       and x["attributes"].get("subtype") in ("TV", "movie", "ONA", "OVA")
                       and any(q in t or (main_key and t.startswith(main_key)) for t in _titles(x))][:4]
    out["episodes"] = []
    for x in franchise:
        xa = x["attributes"]
        if xa.get("posterImage"):
            out["poster"].append(xa["posterImage"].get("original") or xa["posterImage"].get("large"))
        if xa.get("coverImage"):
            out["cover"].append(xa["coverImage"].get("original") or xa["coverImage"].get("large"))
        eps = _get(f"{KITSU}/anime/{x['id']}/episodes", {"page[limit]": 20})
        for e in (eps or {}).get("data", []):
            th = (e["attributes"].get("thumbnail") or {}).get("original")
            if th:
                out["episodes"].append(th)
    ch = _get(f"{KITSU}/anime/{a['id']}/characters",
              {"include": "character", "page[limit]": 20})
    if ch:
        for inc in ch.get("included", []):
            if inc.get("type") != "characters":
                continue
            ia = inc["attributes"]
            img = (ia.get("image") or {}).get("original")
            if img:
                out["characters"][ia.get("canonicalName") or ia.get("name")] = img
    return out


# --------------------------------------------------------------------- Jikan
def jikan_images(query: str) -> dict:
    out = {"poster": [], "pictures": [], "characters": {}}
    d = _get(f"{JIKAN}/anime", {"q": query, "limit": 3, "order_by": "members", "sort": "desc"})
    if not d or not d.get("data"):
        return out
    a = d["data"][0]
    mid = a["mal_id"]
    out["poster"].append(a["images"]["jpg"].get("large_image_url"))
    time.sleep(0.5)
    p = _get(f"{JIKAN}/anime/{mid}/pictures")
    if p:
        out["pictures"] = [x["jpg"].get("large_image_url") for x in p.get("data", [])][:12]
    time.sleep(0.5)
    c = _get(f"{JIKAN}/anime/{mid}/characters")
    if c:
        for x in sorted(c.get("data", []), key=lambda x: -(x.get("favorites") or 0))[:25]:
            name = x["character"]["name"]  # "Gojo, Satoru"
            if "," in name:
                last, first = [s.strip() for s in name.split(",", 1)]
                name = f"{first} {last}"
            out["characters"][name] = x["character"]["images"]["jpg"]["image_url"]
    return out


# ------------------------------------------------------------------ public API
def collect(animes: list[str], workdir: Path) -> dict:
    """Télécharge un pool d'images pour chaque anime. Retourne un index JSON."""
    img_dir = workdir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    index: dict = {}
    for name in animes:
        k = kitsu_images(name)
        j = jikan_images(name)
        entry = {"meta": k.get("anime"), "wide": [], "tall": [], "characters": {}, "sources": []}
        for url in k["cover"] + k.get("episodes", [])[:40]:
            p = _download(url, img_dir)
            if p:
                entry["wide"].append(str(p))
        for url in k["poster"] + j["poster"] + j["pictures"]:
            p = _download(url, img_dir)
            if p and str(p) not in entry["tall"]:
                entry["tall"].append(str(p))
        chars = {**k["characters"], **j["characters"]}
        for cname, url in list(chars.items())[:30]:
            p = _download(url, img_dir)
            if p:
                entry["characters"][cname] = str(p)
        if k.get("anime"):
            entry["sources"].append(k["anime"]["source"])
        if j["poster"]:
            entry["sources"].append("MyAnimeList via Jikan")
        index[name] = entry
    (workdir / "images.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
    return index


def pick(index: dict, anime: str, kind: str = "any", character: str | None = None,
         used: list | None = None) -> str | None:
    """Choisit une image : personnage demandé > type demandé > pool mélangé.
    Évite les répétitions ; quand tout a servi, reprend la moins récente."""
    used = used if used is not None else []
    e = index.get(anime) or next(iter(index.values()), None)
    if not e:
        return None
    cands: list[str] = []
    if character:
        parts = [_norm(w) for w in character.split() if len(w) > 2]
        for name, p in e["characters"].items():
            n = _norm(name)
            if any(pt in n for pt in parts):
                cands.append(p)
    if kind == "wide":
        cands += e["wide"]
    elif kind == "poster":
        cands += e["tall"]
    elif kind == "character":
        cands += list(e["characters"].values())
    pool = []
    for lst in (e["wide"], e["tall"], list(e["characters"].values())):
        pool += lst
    # mélange déterministe : alterne les types
    mixed = [x for trio in zip(e["wide"] + [None] * 60, e["tall"] + [None] * 60,
                               list(e["characters"].values()) + [None] * 60) for x in trio if x]
    for p in cands + mixed + pool:
        if p not in used:
            used.append(p)
            return p
    if not used:
        return None
    p = used.pop(0)  # la plus ancienne
    used.append(p)
    return p
