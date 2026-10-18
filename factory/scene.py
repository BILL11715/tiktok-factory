"""Choisir la bonne scène au bon moment : chaque extrait vidéo est « regardé » par un petit
modèle image-texte (CLIP, version ONNX quantifiée de 150 Mo, CPU), et chaque segment du
script décrit en anglais la scène qu'on veut voir (champ "scene"). Le montage prend
l'extrait dont l'image ressemble le plus à la description : un combat quand on parle de
combat, des larmes quand on parle d'un perso qui craque, et pas un plan d'opening au hasard.

Sans le modèle (réseau coupé), tout continue comme avant : les extraits sont pris dans l'ordre.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import numpy as np

CACHE = Path(os.environ.get("TF_CACHE", Path.home() / ".cache" / "tiktok-factory")) / "clip"
HF = "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/"
FILES = {"vision_model_quantized.onnx": "onnx/vision_model_quantized.onnx",
         "text_model_quantized.onnx": "onnx/text_model_quantized.onnx",
         "tokenizer.json": "tokenizer.json"}
MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

_V = _T = _TOK = None


def available() -> bool:
    try:
        _load()
        return True
    except Exception as exc:
        print(f"[scene] modèle image-texte indisponible ({exc}), extraits pris dans l'ordre")
        return False


def _load():
    global _V, _T, _TOK
    if _V is not None:
        return
    import onnxruntime as ort  # type: ignore
    from tokenizers import Tokenizer  # type: ignore
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, remote in FILES.items():
        dst = CACHE / name
        if not dst.exists() or dst.stat().st_size < 1000:
            part = dst.with_suffix(f".part{os.getpid()}")  # écriture atomique (setup et rendu en parallèle)
            subprocess.run(["curl", "-sL", "--fail", "-m", "600", "-o", str(part), HF + remote], check=True)
            part.replace(dst)
    so = ort.SessionOptions()
    so.intra_op_num_threads = 2
    _V = ort.InferenceSession(str(CACHE / "vision_model_quantized.onnx"), so)
    _T = ort.InferenceSession(str(CACHE / "text_model_quantized.onnx"), so)
    _TOK = Tokenizer.from_file(str(CACHE / "tokenizer.json"))
    _TOK.enable_truncation(77)
    _TOK.enable_padding(length=77, pad_id=49407)


def _prep(img) -> np.ndarray:
    from PIL import Image  # type: ignore
    im = img.convert("RGB")
    s = 224 / min(im.size)
    im = im.resize((max(224, round(im.width * s)), max(224, round(im.height * s))), Image.BICUBIC)
    l, t = (im.width - 224) // 2, (im.height - 224) // 2
    a = np.asarray(im.crop((l, t, l + 224, t + 224)), dtype=np.float32) / 255.0
    return ((a - MEAN) / STD).transpose(2, 0, 1)


def _norm(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)


def embed_frames(video: Path, times: list[float]) -> list[float] | None:
    """Vecteur moyen de quelques images d'une vidéo (cadre d'origine, avant recadrage 9:16)."""
    from PIL import Image  # type: ignore
    import io
    _load()
    batch = []
    for t in times:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                              "-vf", "scale=-2:256", "-f", "image2", "-c:v", "png", "-"],
                             capture_output=True).stdout
        if raw:
            batch.append(_prep(Image.open(io.BytesIO(raw))))
    if not batch:
        return None
    e = _V.run(None, {"pixel_values": np.stack(batch)})[0]
    v = _norm(_norm(e).mean(axis=0))
    return [round(float(x), 4) for x in v]


def embed_texts(texts: list[str]) -> np.ndarray:
    _load()
    ids = np.array([enc.ids for enc in _TOK.encode_batch(texts)], dtype=np.int64)
    return _norm(_T.run(None, {"input_ids": ids})[0])


def release() -> None:
    """Libère le modèle (avant le montage, qui a besoin de toute la mémoire)."""
    global _V, _T, _TOK
    _V = _T = _TOK = None
    import gc
    gc.collect()


# Les descriptions sont complétées par le style, CLIP comprend mieux.
def query(text: str) -> str:
    return f"an anime screenshot of {text.strip().rstrip('.')}"
