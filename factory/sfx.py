"""Bruitages générés par synthèse (aucun fichier externe, aucun droit à gérer)."""
from __future__ import annotations

import subprocess
from pathlib import Path

SR = 44100
SPECS = {
    # whoosh : bruit filtré dont la bande balaye vers le haut
    "whoosh": ("anoisesrc=d=0.5:c=pink:a=0.9",
               "highpass=f=250,lowpass=f=6000,bandpass=f=1400:width_type=o:w=2.5,"
               "afade=t=in:st=0:d=0.22:curve=exp,afade=t=out:st=0.25:d=0.25,volume=1.4"),
    "swoosh": ("anoisesrc=d=0.28:c=white:a=0.7",
               "highpass=f=1200,lowpass=f=9000,afade=t=in:d=0.08,afade=t=out:st=0.1:d=0.18,volume=0.9"),
    "impact": ("sine=f=48:d=0.9",
               "volume=2.2,afade=t=out:st=0.04:d=0.85,aecho=0.6:0.4:40:0.35"),
    "boom": ("sine=f=40:d=1.4",
             "volume=2.6,afade=t=out:st=0.05:d=1.3,aecho=0.8:0.6:60|120:0.4|0.25"),
    "riser": ("anoisesrc=d=1.3:c=pink:a=0.6",
              "highpass=f=400,afade=t=in:st=0:d=1.25:curve=exp,volume=1.1"),
    "glitch": ("anoisesrc=d=0.3:c=white:a=0.8",
               "acrusher=bits=4:mode=log:aa=1:samples=20,tremolo=f=38:d=1,afade=t=out:st=0.18:d=0.12,volume=0.7"),
    "click": ("sine=f=2400:d=0.05", "afade=t=out:st=0.005:d=0.045,volume=0.9"),
    "pop": ("sine=f=880:d=0.14", "afade=t=out:st=0.01:d=0.13,vibrato=f=18:d=0.9,volume=0.8"),
}


def make_all(dest: Path) -> dict[str, Path]:
    dest.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, (src, af) in SPECS.items():
        p = dest / f"{name}.wav"
        if not p.exists():
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src, "-af", af,
                            "-ar", str(SR), "-ac", "1", str(p)], check=True)
        out[name] = p
    return out
