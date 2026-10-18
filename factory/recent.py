"""Ce qui a déjà été traité récemment, pour éviter la redondance.

Usage : python3 -m factory.recent   -> franchises et formats des 14 derniers jours, avec la
liste des franchises INTERDITES pour la prochaine vidéo (déjà traitées il y a moins de 7 jours).
"""
from __future__ import annotations

import collections
import datetime as dt
import json
from pathlib import Path

from .clips import base_title

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    today = dt.date.today()
    rows = []
    for line in (ROOT / "history.jsonl").read_text().splitlines():
        try:
            d = json.loads(line)
            day = dt.date.fromisoformat(d.get("slot", d.get("stamp", ""))[:10])
        except Exception:
            continue
        if (today - day).days <= 14:
            rows.append((day, d))
    fr = collections.Counter(base_title(d.get("anime", "")) for _, d in rows)
    blocked = sorted({base_title(d.get("anime", "")) for day, d in rows if (today - day).days < 7})
    fmt = collections.Counter(d.get("format") for day, d in rows if (today - day).days < 7)
    media = collections.Counter(d.get("media", "anime") for day, d in rows if (today - day).days < 7)
    print("Franchises des 14 derniers jours :", ", ".join(f"{k} x{v}" for k, v in fr.most_common()))
    print("INTERDITES pour cette vidéo (traitées il y a moins de 7 jours) :", ", ".join(blocked) or "aucune")
    print("Formats sur 7 jours :", dict(fmt))
    print("Supports sur 7 jours :", dict(media), "(objectif : au moins 1 manhwa par jour)")


if __name__ == "__main__":
    main()
