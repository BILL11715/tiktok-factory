"""Texte "prononçable" pour la voix (Kyutai, Gemini) : prix, nombres, pourcentages, unités et
mots du lexique (config/prononciation.json) écrits en toutes lettres. Ne sert qu'à la voix :
les sous-titres et l'écran gardent le texte du script.

Le lexique s'enrichit au fil des audits (factory/audit.py) : un mot mal compris par la
transcription sur plusieurs vidéos y reçoit une écriture phonétique.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LEXICON = Path(__file__).resolve().parent.parent / "config" / "prononciation.json"


def _n2w(x: str, ordinal: bool = False) -> str:
    try:
        from num2words import num2words  # type: ignore
    except Exception:
        return x
    s = x.replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        if ordinal:
            return num2words(int(s), lang="fr", to="ordinal")
        v = float(s)
        if v.is_integer():
            v = int(v)
        return num2words(v, lang="fr")
    except Exception:
        return x


NUM = r"\d{1,3}(?:[  ]\d{3})+|\d+(?:[.,]\d+)?"


def lexicon(path: Path | None = None) -> dict:
    try:
        d = json.loads((path or LEXICON).read_text())
        return {k: v for k, v in d.items() if not k.startswith("_")}
    except Exception:
        return {}


def speakable(text: str, lexicon_file: Path | None = None) -> str:
    """lexicon_file : lexique propre à une voix (Gemini : config/prononciation_gemini.json),
    sinon celui de Kyutai (config/prononciation.json)."""
    t = text
    # mots du lexique (mot entier, sensible à la casse pour les sigles)
    for src, dst in sorted(lexicon(lexicon_file).items(), key=lambda kv: -len(kv[0])):
        t = re.sub(rf"(?<![\w-]){re.escape(src)}(?![\w-])", dst, t)
    # unités collées aux prix : "19 €/mois", "49€ par mois", "2 k€"
    t = re.sub(rf"({NUM})\s?k€", lambda m: f"{_n2w(m.group(1))} mille euros", t)
    t = re.sub(rf"({NUM})\s?€\s?/\s?mois", lambda m: f"{_n2w(m.group(1))} euros par mois", t)
    t = re.sub(rf"({NUM})\s?€\s?HT", lambda m: f"{_n2w(m.group(1))} euros hors taxes", t)
    t = re.sub(rf"({NUM})\s?€", lambda m: f"{_n2w(m.group(1))} euros", t)
    t = re.sub(rf"({NUM})\s?\$", lambda m: f"{_n2w(m.group(1))} dollars", t)
    t = re.sub(rf"({NUM})\s?%", lambda m: f"{_n2w(m.group(1))} pour cent", t)
    t = re.sub(rf"({NUM})\s?/\s?(\d+)", lambda m: f"{_n2w(m.group(1))} sur {_n2w(m.group(2))}", t)
    t = re.sub(r"\b(\d+)(?:er|ère|e|ème)\b", lambda m: _n2w(m.group(1), ordinal=True), t)
    t = re.sub(r"\b(\d+)\s?h\s?(\d{2})\b", lambda m: f"{_n2w(m.group(1))} heures {_n2w(m.group(2))}", t)
    t = re.sub(r"\b(\d+)\s?h\b", lambda m: f"{_n2w(m.group(1))} heures", t)
    t = re.sub(r"\b(\d+)\s?k\b", lambda m: f"{_n2w(m.group(1))} mille", t)
    # nombres restants
    t = re.sub(NUM, lambda m: _n2w(m.group(0)), t)
    t = re.sub(r"\s=\s", " égale ", t)
    t = t.replace("€", " euros").replace("%", " pour cent").replace("&", " et ")
    return re.sub(r"\s+", " ", t).strip()


if __name__ == "__main__":
    import sys
    print(speakable(" ".join(sys.argv[1:])))
