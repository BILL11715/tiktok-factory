"""Netteté de la voix : traitement commun à tous les montages (Asura et iafortous).

Constat mesuré sur les vidéos du 10/10 : le clone Fish reproduit le grave gonflé de
l'échantillon d'origine (fondamental vers 100 Hz 10 dB au-dessus du reste) et manque de
médiums-aigus (1 à 4 kHz, la zone des consonnes). Résultat : voix lourde, étouffée, et
le compresseur + loudnorm dynamique remontaient le souffle et le fond sonore.

Chaîne appliquée ici, une seule fois, sur la voix complète :
  1. coupe-bas + atténuation du grave gonflé (fini le côté "lourd")
  2. léger débruitage (souffle du clone)
  3. présence : boost large 1,5 à 4 kHz (intelligibilité), un peu d'air
  4. dé-esseur puis compression douce
  5. gain FIXE calculé sur la mesure réelle (pas de loudnorm dynamique qui pompe),
     limiteur de sécurité
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

VOICE_LUFS = float(os.environ.get("TF_VOICE_LUFS", "-14.5"))  # niveau de la voix dans le mix

VOICE_EQ = (
    "highpass=f=85:p=2,"
    "lowshelf=f=170:g=-8:t=q:w=0.7,"          # grave gonflé du clone
    "equalizer=f=320:t=q:w=1.0:g=-2,"         # boîte / côté sourd
    "afftdn=nr=8:nf=-55:tn=0,"                # souffle
    "equalizer=f=1500:t=q:w=0.9:g=3,"         # corps des consonnes
    "equalizer=f=2600:t=q:w=0.9:g=5,"         # présence, articulation
    "highshelf=f=9000:g=1.5:t=q:w=0.7,"         # air
    "equalizer=f=6000:t=q:w=1.2:g=-3,"          # sifflantes du clone
    "deesser=i=0.3:m=0.5:f=0.5:s=o,"
    "acompressor=threshold=0.09:ratio=2.5:attack=8:release=140:makeup=1"
)


def _loudness(path: Path, af: str = "") -> float:
    """Loudness intégrée (LUFS) du fichier, après le filtre `af` éventuel."""
    chain = (af + "," if af else "") + "ebur128"
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", chain,
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    return float(m[-1]) if m else -20.0


def clean_voice(src: Path, dst: Path) -> Path:
    """Voix nette et à niveau constant (mono 44,1 kHz). En cas d'erreur, renvoie la voix brute."""
    src, dst = Path(src), Path(dst)
    try:
        gain = max(-6.0, min(VOICE_LUFS - _loudness(src, VOICE_EQ), 24.0))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af",
                        f"{VOICE_EQ},volume={gain:.2f}dB,alimiter=limit=0.8:attack=3:release=60:level=false",
                        "-ar", "44100", "-ac", "1", str(dst)], check=True)
        return dst
    except Exception as exc:  # ne jamais bloquer un rendu pour ça
        print(f"[audio] traitement de la voix impossible ({exc}), voix brute")
        return src
