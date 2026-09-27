"""Animes du moment : saison en cours (en diffusion) et à venir (annoncés), via AniList.

Usage : python -m factory.season   -> écrit /tmp/tf-season.json et affiche une liste courte
que l'agent utilise pour choisir l'anime d'une reco (priorité aux nouveautés).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.request

Q = """
query ($status: MediaStatus, $season: MediaSeason, $year: Int, $page: Int) {
  Page(page: $page, perPage: 30) {
    media(type: ANIME, status: $status, season: $season, seasonYear: $year, sort: [POPULARITY_DESC],
          isAdult: false, format_in: [TV, TV_SHORT, ONA, MOVIE]) {
      id title { romaji english } format status episodes popularity trending averageScore
      season seasonYear startDate { year month day } genres
      nextAiringEpisode { episode airingAt }
      relations { edges { relationType node { title { romaji english } type } } }
      description(asHtml: false)
    }
  }
}"""


def _q(variables: dict) -> list[dict]:
    req = urllib.request.Request("https://graphql.anilist.co", method="POST",
                                 data=json.dumps({"query": Q, "variables": variables}).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": "tiktok-factory/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["data"]["Page"]["media"]


def _season(d: dt.date) -> tuple[str, int]:
    return (["WINTER"] * 3 + ["SPRING"] * 3 + ["SUMMER"] * 3 + ["FALL"] * 3)[d.month - 1], d.year


def _next(season: str, year: int) -> tuple[str, int]:
    order = ["WINTER", "SPRING", "SUMMER", "FALL"]
    i = order.index(season)
    return (order[(i + 1) % 4], year + (1 if i == 3 else 0))


def _item(m: dict, kind: str) -> dict:
    sequel_of = [e["node"]["title"]["english"] or e["node"]["title"]["romaji"]
                 for e in (m.get("relations") or {}).get("edges", [])
                 if e["relationType"] == "PREQUEL" and e["node"]["type"] == "ANIME"]
    sd = m.get("startDate") or {}
    return {"kind": kind, "anilist_id": m["id"], "title": m["title"]["english"] or m["title"]["romaji"],
            "romaji": m["title"]["romaji"], "format": m["format"], "popularity": m["popularity"],
            "trending": m.get("trending"), "score": m.get("averageScore"),
            "start": f"{sd.get('year')}-{sd.get('month') or 0:02d}-{sd.get('day') or 0:02d}",
            "episodes": m.get("episodes"), "next_ep": (m.get("nextAiringEpisode") or {}).get("episode"),
            "genres": m.get("genres", [])[:4], "suite_de": sequel_of[:1],
            "pitch": (m.get("description") or "").replace("<br>", " ")[:300]}


def main() -> list[dict]:
    today = dt.date.today()
    cur, year = _season(today)
    nxt, nyear = _next(cur, year)
    out = [_item(m, "en_cours") for m in _q({"status": "RELEASING", "season": cur, "year": year, "page": 1})]
    out += [_item(m, "a_venir") for m in _q({"status": "NOT_YET_RELEASED", "season": nxt, "year": nyear, "page": 1})]
    # suites très attendues sans saison fixée (annoncées)
    out += [_item(m, "annonce") for m in _q({"status": "NOT_YET_RELEASED", "page": 1})
            if not m.get("season") and m["popularity"] > 40000][:15]
    seen, uniq = set(), []
    for x in out:
        if x["popularity"] < 5000:  # trop confidentiel pour un compte FR
            continue
        if x["anilist_id"] not in seen:
            seen.add(x["anilist_id"])
            uniq.append(x)
    with open("/tmp/tf-season.json", "w") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=1)
    for x in uniq:
        suite = f" (suite de {x['suite_de'][0]})" if x["suite_de"] else ""
        print(f"[{x['kind']}] {x['title']}{suite} | début {x['start']} | pop {x['popularity']} | {', '.join(x['genres'])}")
    return uniq


if __name__ == "__main__":
    main()
    sys.exit(0)
