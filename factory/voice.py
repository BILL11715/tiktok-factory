"""Voix off : clone de la voix de Bill (Chatterbox multilingue), secours Piper.

Chaque segment du script est synthétisé séparément, ce qui donne la durée
exacte de chaque phrase (utile pour caler sous-titres et visuels sans
transcription).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import wave
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(os.environ.get("TF_CACHE", Path.home() / ".cache" / "tiktok-factory"))
VOICE_REF = ROOT / "voice" / "bill_reference.wav"
PIPER_VOICE = "fr-gilles-low"  # voix masculine FR, servie par GitHub (pas HuggingFace)
PIPER_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-fr-gilles-low.tar.gz"

# Réglages de ton par format : (exaggeration, cfg_weight, vitesse piper)
TONES = {
    "pote": (0.55, 0.5, 1.0),
    "conteur": (0.4, 0.35, 1.12),
    "hype": (0.75, 0.55, 0.92),
    "pose": (0.35, 0.3, 1.18),
}


def _dur(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


# ------------------------------------------------------------------ Chatterbox
_CB = None


def _chatterbox():
    global _CB
    if _CB is None:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # type: ignore
        _CB = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    return _CB


def _sentences(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
    return parts or [text]


_CONDS: dict = {}
CHARS_PER_SEC = 19.0  # débit mesuré de la voix clonée (caractères par seconde)


def _tts_chatterbox(text: str, out: Path, tone: str) -> None:
    """Phrase par phrase, avec contrôle de durée : une phrase qui boucle ou qui est
    coupée (durée incohérente avec le texte) est régénérée, on garde la plus plausible."""
    import logging
    import torch  # type: ignore
    import torchaudio  # type: ignore
    logging.getLogger("chatterbox").setLevel(logging.ERROR)
    ex, cfg, _ = TONES.get(tone, TONES["pote"])
    model = _chatterbox()
    if ex not in _CONDS:
        model.prepare_conditionals(str(VOICE_REF), exaggeration=ex)
        _CONDS[ex] = model.conds
    model.conds = _CONDS[ex]
    pieces = []
    for sent in _sentences(text):
        expected = max(len(sent) / CHARS_PER_SEC, 0.6)
        best, best_err = None, 1e9
        for attempt in range(3):
            torch.manual_seed(1234 + attempt * 97 + len(sent))
            wav = model.generate(sent, language_id="fr", exaggeration=ex, cfg_weight=cfg,
                                 temperature=0.7 if attempt else 0.8)
            dur = wav.shape[1] / model.sr
            err = abs(dur - expected) / expected
            if err < best_err:
                best, best_err = wav, err
            if 0.55 * expected <= dur <= 1.6 * expected + 0.8:
                break
        if best_err > 1.0:  # toujours incohérent : on coupe la traîne
            best = best[:, : int(model.sr * (expected * 1.5 + 0.5))]
        pieces.append(best)
        pieces.append(torch.zeros(1, int(model.sr * 0.12)))
    torchaudio.save(str(out), torch.cat(pieces[:-1], dim=1), model.sr)


# ------------------------------------------------------------------ Piper
def _piper_model() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    onnx = CACHE / f"{PIPER_VOICE}.onnx"
    if not onnx.exists():
        tgz = CACHE / "piper_voice.tar.gz"
        subprocess.run(["curl", "-sL", "--fail", "-o", str(tgz), PIPER_URL], check=True)
        subprocess.run(["tar", "xzf", str(tgz), "-C", str(CACHE)], check=True)
    return onnx


def _tts_piper(text: str, out: Path, tone: str) -> None:
    from piper import PiperVoice  # type: ignore
    from piper.config import SynthesisConfig  # type: ignore
    voice = PiperVoice.load(str(_piper_model()))
    speed = TONES.get(tone, TONES["pote"])[2]
    with wave.open(str(out), "wb") as wf:
        voice.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=speed))


# ------------------------------------------------------------------ public
def engine() -> str:
    forced = os.environ.get("TF_VOICE")
    flag = Path("/tmp/tf-voice-engine")
    if not forced and flag.exists():
        forced = flag.read_text().strip()
    if forced:
        return forced
    if not VOICE_REF.exists():
        return "piper"
    try:
        import chatterbox  # noqa: F401  # type: ignore
        return "clone"
    except Exception:
        return "piper"


def synthesize(segments: list[dict], workdir: Path, tone: str) -> dict:
    """Synthétise chaque segment, ajoute des pauses naturelles, renvoie la timeline."""
    vdir = workdir / "voice"
    vdir.mkdir(parents=True, exist_ok=True)
    eng = engine()
    timeline, files, t = [], [], 0.0
    for i, seg in enumerate(segments):
        raw = vdir / f"seg{i:02d}_raw.wav"
        try:
            if eng == "clone":
                _tts_chatterbox(seg["text"], raw, seg.get("tone", tone))
            else:
                _tts_piper(seg["text"], raw, seg.get("tone", tone))
        except Exception as exc:  # secours automatique
            print(f"[voice] {eng} a échoué ({exc}), passage sur Piper")
            eng = "piper"
            _tts_piper(seg["text"], raw, seg.get("tone", tone))
        # normalisation 44.1k mono + petite pause variable (respiration)
        pause = float(seg.get("pause_after", 0.28 if i < len(segments) - 1 else 0.6))
        clean = vdir / f"seg{i:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
                        f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        f"apad=pad_dur={pause}", "-ar", "44100", "-ac", "1", str(clean)], check=True)
        d = _dur(clean)
        timeline.append({"index": i, "start": round(t, 3), "end": round(t + d - pause, 3),
                         "slot_end": round(t + d, 3), "text": seg["text"]})
        files.append(clean)
        t += d
    lst = vdir / "list.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files))
    voice = workdir / "voice.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(voice)], check=True, cwd=vdir)
    result = {"engine": eng, "path": str(voice), "duration": round(t, 3), "timeline": timeline}
    (workdir / "voice.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return result
