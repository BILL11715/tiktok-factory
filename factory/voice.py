"""Voix off : Gemini TTS « Kore » (@iafortous), clone Fish Audio (@the.asura8), Kyutai
Pocket TTS « estelle », Chatterbox local, secours Piper.

Fish Audio est utilisé dès que la variable d'environnement FISH_API_KEY existe, Gemini dès
que TF_VOICE=gemini (les clés ne doivent JAMAIS être écrites dans le dépôt, qui est public).

Synthèse phrase par phrase : chaque phrase a sa durée exacte, ce qui donne un
minutage mot par mot (sous-titres et changements d'image calés sur la parole)
sans transcription. Débit accéléré et pauses courtes pour un rythme TikTok.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import warnings
import wave
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(os.environ.get("TF_CACHE", Path.home() / ".cache" / "tiktok-factory"))
VOICE_REF = ROOT / "voice" / "bill_reference.wav"
PIPER_VOICE = "fr-gilles-low"  # voix masculine FR, servie par GitHub (pas HuggingFace)
PIPER_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-fr-gilles-low.tar.gz"

FISH_URL = "https://api.fish.audio/v1/tts"
FISH_VOICE = os.environ.get("FISH_VOICE_ID", "b0f4d96b219449c5b6a712e61fb432a4")  # clone "Asura"
FISH_MODELS = [m for m in os.environ.get("FISH_MODEL", "s2-pro,s1").split(",") if m]
TAG_RE = re.compile(r"\[[^\]]{1,30}\]\s*")  # balises d'émotion : [excited], [whispering]...


def _plain(text: str) -> str:
    """Texte sans balises d'émotion (sous-titres, minutage, moteurs locaux)."""
    return re.sub(r"\s+", " ", TAG_RE.sub("", text)).strip()


# Réglages par ton : exaggeration (expressivité), cfg_weight, tempo final, vitesse piper
TONES = {
    "pote": (0.75, 0.5, 1.14, 0.9),
    "hype": (0.95, 0.55, 1.18, 0.85),
    "conteur": (0.6, 0.45, 1.08, 1.0),
    "pose": (0.5, 0.4, 1.0, 1.08),
}
GAP_SENT = 0.05   # silence entre deux phrases d'un segment
GAP_SEG = 0.06    # silence entre deux segments
CHARS_PER_SEC = 19.0  # débit brut du clone avant accélération (contrôle de cohérence)


def _dur(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def _sentences(text: str, min_chars: int = 38) -> list[str]:
    """Découpe en phrases, en regroupant les phrases trop courtes (le modèle
    invente une traîne sur les phrases de 2-3 mots)."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()] or [text]
    out: list[str] = []
    for p in parts:
        if out and (len(out[-1]) < min_chars or len(p) < min_chars) and len(out[-1]) + len(p) < 190:
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return out


# ------------------------------------------------------------------ référence
def reference() -> Path:
    """Extrait de l'échantillon de Bill les ~12 s les plus vivantes (beaucoup de parole,
    énergie variée) : le clone copie le ton de ce passage."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"ref_active_{int(VOICE_REF.stat().st_mtime)}.wav"
    if out.exists():
        return out
    try:
        import numpy as np
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(VOICE_REF), "-ac", "1", "-ar", "16000",
                              "-f", "s16le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
        hop = 1600  # 100 ms
        rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-9) for i in range(0, len(x) - hop, hop)])
        db = 20 * np.log10(rms)
        speech = db > (np.percentile(db, 90) - 25)
        win = 120  # 12 s
        if len(db) <= win:
            raise ValueError("échantillon court")
        best, best_s = 0, -1e9
        for s in range(0, len(db) - win, 5):
            seg_sp = speech[s:s + win]
            score = seg_sp.mean() * 2 + np.std(db[s:s + win][seg_sp]) / 10 if seg_sp.any() else -1
            if score > best_s:
                best, best_s = s, score
        start = best * 0.1
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.2f}", "-t", "12", "-i", str(VOICE_REF),
                        "-af", "silenceremove=stop_periods=-1:stop_duration=0.35:stop_threshold=-45dB",
                        "-ar", "24000", "-ac", "1", str(out)], check=True)
        return out
    except Exception as exc:
        print(f"[voice] sélection de l'extrait impossible ({exc}), échantillon complet")
        return VOICE_REF


# ------------------------------------------------------------------ Chatterbox
_CB = None
_CONDS: dict = {}


def _chatterbox():
    global _CB
    if _CB is None:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # type: ignore
        _CB = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    return _CB


def _tts_chatterbox(sent: str, out: Path, tone: str) -> None:
    """Une phrase, avec contrôle de durée : si elle boucle ou se coupe, on régénère."""
    import logging
    import torch  # type: ignore
    import torchaudio  # type: ignore
    logging.getLogger("chatterbox").setLevel(logging.ERROR)
    ex, cfg, _, _ = TONES.get(tone, TONES["pote"])
    model = _chatterbox()
    if ex not in _CONDS:
        model.prepare_conditionals(str(reference()), exaggeration=ex)
        _CONDS[ex] = model.conds
    model.conds = _CONDS[ex]
    expected = 0.4 + len(sent) / CHARS_PER_SEC
    best, best_err = None, 1e9
    for attempt in range(3):
        torch.manual_seed(1234 + attempt * 97 + len(sent))
        wav = model.generate(sent, language_id="fr", exaggeration=ex, cfg_weight=cfg,
                             temperature=0.8 if attempt == 0 else 0.7)
        dur = wav.shape[1] / model.sr
        err = abs(dur - expected) / expected
        if os.environ.get("TF_DEBUG"):
            print(f"[voice] essai {attempt} {dur:.1f}s / attendu {expected:.1f}s : {sent[:40]}")
        if err < best_err:
            best, best_err = wav, err
        if 0.6 * expected <= dur <= 1.45 * expected + 0.5:
            break
    if best_err > 1.0:  # toujours incohérent : on coupe la traîne
        best = best[:, : int(model.sr * (expected * 1.5 + 0.5))]
    torchaudio.save(str(out), best, model.sr)


# ------------------------------------------------------------------ Fish Audio
FISH_KEY_FILE = Path("/tmp/tf-fish-key")  # écrit par l'agent au début du run, jamais dans le repo


def _fish_key() -> str:
    key = os.environ.get("FISH_API_KEY", "")
    if not key and FISH_KEY_FILE.exists():
        key = FISH_KEY_FILE.read_text().strip()
    return key

# Débit Fish (prosody.speed) : plus rapide qu'avant, rythme TikTok
FISH_SPEED = {"hype": 1.36, "pote": 1.32, "conteur": 1.24, "pose": 1.12}
STRONG = {"excited": "very excited", "surprised": "very surprised", "laughing": "laughing",
          "angry": "very angry", "sad": "very sad", "shouting": "shouting", "whispering": "whispering"}
# intention par défaut des phrases affirmatives, en rotation pour ne jamais rester sur le même ton
MOODS = {"pote": ["energetic", "playful", "confident", "amused"],
         "hype": ["very excited", "energetic", "determined", "very excited"],
         "conteur": ["intrigued", "mysterious", "dramatic", "intrigued"],
         "pose": ["calm", "soft tone", "nostalgic", "calm"]}
_MOOD_I = [0]


def direct(text: str, emphasis: list[str] | None = None, tone: str = "pote") -> str:
    """Mise en scène automatique pour Fish S2 (balises entre crochets) : chaque phrase reçoit
    une intention selon sa ponctuation (exclamation = enthousiasme, question = curiosité ou
    étonnement), les balises du script sont renforcées, et les mots mis en avant à l'écran
    sont aussi accentués à la voix ([emphasis]). Évite la lecture plate et monotone."""
    text = re.sub(r"\[(\w+)\]", lambda m: f"[{STRONG.get(m.group(1).lower(), m.group(1))}]", text)
    parts = [x for x in re.split(r"(?<=[.!?…])\s+", text.strip()) if x]
    out = []
    for i, p in enumerate(parts):
        if not p.startswith("["):
            core = p.rstrip()
            if core.endswith("!"):
                p = "[very excited] " + p
            elif core.endswith("?"):
                p = ("[surprised] " if re.search(r"\b(quoi|vraiment|s[ée]rieux|comment|pourquoi|rends compte|imagine)\b", core, re.I)
                     else "[curious] ") + p
            elif core.endswith("…") or core.endswith("..."):
                p = "[suspenseful] " + p
            elif re.match(r"(mais|sauf que|et là|sauf qu|pourtant|attends)\b", core, re.I):
                p = "[dramatic] " + p
            else:
                moods = MOODS.get(tone, MOODS["pote"])
                p = f"[{moods[_MOOD_I[0] % len(moods)]}] " + p
                _MOOD_I[0] += 1
        out.append(p)
    res = " ".join(out)
    for w in emphasis or []:
        res = re.sub(rf"(?<![\w\[])({re.escape(w)})\b", r"[emphasis] \1", res, count=1, flags=re.I)
    return res


def _tts_fish(sent: str, out: Path, tone: str) -> None:
    """Un segment entier via l'API Fish Audio (le modèle voit toute l'idée : intonation plus
    naturelle qu'en phrases isolées). Les balises d'émotion restent dans le texte."""
    import urllib.request
    import urllib.error
    # Clé soit en variable d'environnement, soit (mieux) en "API credential" de l'environnement
    # cloud : le proxy l'ajoute alors lui-même aux requêtes vers api.fish.audio (TF_VOICE=fish).
    key = _fish_key()
    speed = float(os.environ.get("FISH_SPEED", 0) or FISH_SPEED.get(tone, 1.18))
    body = json.dumps({"text": sent, "reference_id": FISH_VOICE, "format": "mp3",
                       "mp3_bitrate": 192, "latency": "normal", "normalize": True,
                       # un peu plus de liberté au modèle = intonation plus vivante
                       "temperature": 1.0, "top_p": 0.9,
                       "prosody": {"speed": speed}}).encode()
    last = None
    for model in FISH_MODELS:
        headers = {"Content-Type": "application/json", "model": model}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        req = urllib.request.Request(FISH_URL, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                mp3 = out.with_suffix(".mp3")
                mp3.write_bytes(r.read())
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "44100", "-ac", "1",
                            str(out)], check=True)
            return
        except urllib.error.HTTPError as exc:  # modèle inconnu : on tente le suivant
            last = RuntimeError(f"Fish {model} HTTP {exc.code}: {exc.read()[:200]!r}")
            if exc.code in (401, 402, 403):  # clé invalide ou crédits épuisés : inutile d'insister
                break
    raise last or RuntimeError("Fish Audio indisponible")


# ------------------------------------------------------------------ Kyutai Pocket TTS (local, CPU)
# Voix choisie par Bill pour @iafortous : "estelle" (français, modèle french_24l).
# Licence CC-BY-4.0 : créditer Kyutai (bio du compte). Poids téléchargés depuis Hugging Face.
KYUTAI_LANG = os.environ.get("KYUTAI_LANG", "french_24l")
KYUTAI_VOICE = os.environ.get("KYUTAI_VOICE", "estelle")
KYUTAI_OK = Path("/tmp/tf-kyutai-ok")  # écrit par setup.sh quand le modèle est prêt
GAPS = {"kyutai": (0.22, 0.36)}  # (entre deux phrases, entre deux segments) : respiration naturelle
# un chouïa plus lent que la voix brute (retour de Bill : trop rapide, brusque) ; atempo garde le timbre
KYUTAI_TEMPO = float(os.environ.get("KYUTAI_TEMPO", "0.94"))
_KYU = None


def _tts_kyutai(sent: str, out: Path, tone: str) -> None:
    global _KYU
    import numpy as np  # type: ignore
    if _KYU is None:
        from pocket_tts import TTSModel  # type: ignore
        m = TTSModel.load_model(language=KYUTAI_LANG)
        _KYU = (m, m.get_state_for_audio_prompt(KYUTAI_VOICE))
    m, st = _KYU
    from .pronounce import speakable
    audio = m.generate_audio(st, speakable(sent)).numpy()
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(m.sample_rate))
        wf.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ Gemini TTS (API Google)
# Voix choisie par Bill pour @iafortous le 26/10/2026 : Gemini 3.8 Flash TTS, voix « Kore »
# (femme, ferme et assurée). Clé : variable GEMINI_API_KEY ou fichier /tmp/tf-gemini-key écrit
# par l'agent au début du run (jamais dans le repo). Sans clé, la requête part sans en-tête :
# utile si la clé est enregistrée comme "API credential" de l'environnement (ajoutée par le proxy).
# Tout le texte part en UN appel : intonation continue d'une phrase à l'autre, et le quota
# gratuit compte les requêtes par jour. Les débuts de segments sont ensuite recalés sur la voix
# réelle par l'alignement Whisper (align.align puis reslot).
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODELS = [m.strip() for m in os.environ.get(
    "GEMINI_TTS_MODEL", "gemini-3.8-flash-tts,gemini-3.8-flash-lite-tts").split(",") if m.strip()]
GEMINI_VOICE = os.environ.get("GEMINI_VOICE", "Kore")
# consigne de jeu (speech_metadata.style) : courte, la doc Google déconseille les longues consignes
GEMINI_STYLE = os.environ.get(
    "GEMINI_STYLE",
    "French TikTok tech creator explaining to a friend: warm, confident and upbeat, "
    "lively pace but clearly articulated, natural intonation on questions and exclamations")
GEMINI_TEMPO = float(os.environ.get("GEMINI_TEMPO", "1.0"))
GEMINI_BLOCK = int(os.environ.get("GEMINI_BLOCK_CHARS", "2200"))  # au-delà : plusieurs appels
GEMINI_GAP = 0.3  # silence entre deux blocs (seulement si le texte a dû être coupé)
GEMINI_KEY_FILE = Path("/tmp/tf-gemini-key")
GEMINI_OK = Path("/tmp/tf-gemini-ok")  # écrit par setup.sh quand l'API répond
GEMINI_RATE = 24000
GEMINI_LEXICON = ROOT / "config" / "prononciation_gemini.json"


def _gemini_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key and GEMINI_KEY_FILE.exists():
        key = GEMINI_KEY_FILE.read_text().strip()
    return key


def _pcm(blob: bytes) -> tuple[bytes, int]:
    """(PCM 16 bits mono, fréquence) depuis du WAV (en-tête RIFF) ou du PCM brut 24 kHz."""
    if blob[:4] == b"RIFF":
        with wave.open(io.BytesIO(blob)) as wf:
            return wf.readframes(wf.getnframes()), wf.getframerate()
    return blob, GEMINI_RATE


def _post(url: str, body: dict, key: str, timeout: int = 300) -> dict:
    import urllib.request
    headers = {"Content-Type": "application/json"}
    if key:
        headers["x-goog-api-key"] = key
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _gemini_interactions(text: str, model: str, key: str) -> list[bytes]:
    """API Interactions (modèles Gemini 3.8 TTS) : le texte est lu tel quel, la consigne de jeu
    passe dans speech_metadata.style."""
    part: dict = {"type": "text", "text": text}
    if GEMINI_STYLE:
        part["annotations"] = [{"type": "speech_metadata", "style": GEMINI_STYLE}]
    data = _post(f"{GEMINI_API}/interactions", {
        "model": model,
        "input": [{"type": "user_input", "content": [part]}],
        "response_format": {"type": "audio", "mime_type": "audio/wav", "sample_rate": GEMINI_RATE},
        "generation_config": {"speech_config": [{"voice": GEMINI_VOICE}]},
    }, key)
    out = []
    for step in data.get("steps") or []:
        for c in step.get("content") or []:
            if c.get("type") == "audio" and c.get("data"):
                out.append(base64.b64decode(c["data"]))
    if not out and (data.get("output_audio") or {}).get("data"):
        out.append(base64.b64decode(data["output_audio"]["data"]))
    return out


def _gemini_generate(text: str, model: str, key: str) -> list[bytes]:
    """Ancienne API generateContent (secours si Interactions refuse la requête), sans consigne
    de jeu : les modèles TTS récents la liraient à voix haute."""
    data = _post(f"{GEMINI_API}/models/{model}:generateContent", {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
            "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GEMINI_VOICE}}}},
    }, key)
    out = []
    for cand in data.get("candidates") or []:
        for p in (cand.get("content") or {}).get("parts") or []:
            inline = p.get("inlineData") or p.get("inline_data") or {}
            if inline.get("data"):
                out.append(base64.b64decode(inline["data"]))
    return out


def _tts_gemini(text: str, out: Path) -> None:
    """Un bloc de texte (en général le script entier) en un appel. Essaie chaque modèle, et
    l'API generateContent si Interactions refuse la requête. Erreur détaillée si tout échoue."""
    import time
    import urllib.error
    key = _gemini_key()
    errors: list[str] = []
    for model in GEMINI_MODELS:
        for call in (_gemini_interactions, _gemini_generate):
            api = call.__name__.replace("_gemini_", "")
            for attempt in range(2):
                try:
                    blobs = call(text, model, key)
                    if not blobs:
                        raise RuntimeError("réponse sans audio")
                    frames, rate = b"", GEMINI_RATE
                    for b in blobs:
                        f, rate = _pcm(b)
                        frames += f
                    with wave.open(str(out), "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(rate)
                        wf.writeframes(frames)
                    print(f"[voice] gemini {model} ({api}), voix {GEMINI_VOICE}")
                    return
                except urllib.error.HTTPError as exc:
                    msg = exc.read()[:300].decode("utf-8", "replace")
                    errors.append(f"{model} {api} HTTP {exc.code}: {msg}")
                    if exc.code in (401, 403):  # clé refusée : inutile d'insister
                        raise RuntimeError(" | ".join(errors)[:900])
                    if exc.code in (500, 502, 503, 504) and attempt == 0:
                        time.sleep(8)
                        continue
                    break  # 400 / 404 : on tente l'autre API ; 429 (quota) : l'autre modèle
                except Exception as exc:  # réseau bloqué, délai dépassé, réponse inattendue
                    errors.append(f"{model} {api}: {exc}")
                    if attempt == 0 and "timed out" in str(exc):
                        continue
                    break
            if errors and "HTTP 429" in errors[-1]:
                break  # quota du modèle épuisé : l'autre API puise dans le même quota
    raise RuntimeError(" | ".join(errors)[:900] or "Gemini indisponible")


def _gemini_blocks(segments: list[dict]) -> list[list[int]]:
    """Regroupe les segments en blocs de GEMINI_BLOCK caractères max (en pratique : un seul)."""
    blocks: list[list[int]] = []
    cur: list[int] = []
    size = 0
    for i, seg in enumerate(segments):
        n = len(_plain(seg["text"]))
        if cur and size + n > GEMINI_BLOCK:
            blocks.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += n
    if cur:
        blocks.append(cur)
    return blocks


def _synthesize_gemini(segments: list[dict], workdir: Path, lead: float) -> dict:
    from .pronounce import speakable
    vdir = workdir / "voice"
    vdir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    t = 0.0
    if lead > 0:
        sil = vdir / "lead.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-t", f"{lead:.2f}", str(sil)], check=True)
        files.append(sil)
        t = _dur(sil)

    def render(idx: list[int], depth: int = 0) -> list[tuple[list[int], Path]]:
        """Synthétise un bloc ; s'il revient tronqué ou anormalement long, le coupe en deux."""
        segs = [segments[i] for i in idx]
        chars = sum(len(_plain(s["text"])) for s in segs)
        raw = vdir / f"g{idx[0]:02d}-{idx[-1]:02d}_raw.wav"
        # un segment par ligne : le retour à la ligne donne une respiration entre deux idées
        _tts_gemini("\n".join(speakable(_plain(s["text"]), lexicon_file=GEMINI_LEXICON) for s in segs), raw)
        d = _dur(raw)
        if chars / 30 <= d <= chars / 6 + 3:
            return [(idx, raw)]
        print(f"[voice] gemini : {d:.1f} s pour {chars} car. (tronqué ou dérive), bloc recoupé")
        if len(idx) > 1 and depth < 3:
            h = len(idx) // 2
            return render(idx[:h], depth + 1) + render(idx[h:], depth + 1)
        raise RuntimeError(f"audio incohérent ({d:.1f} s pour {chars} car.)")

    parts: list[tuple[list[int], Path]] = []
    for block in _gemini_blocks(segments):
        parts += render(block)
    timeline: list[dict] = []
    for k, (idx, raw) in enumerate(parts):
        gap = 0.7 if k == len(parts) - 1 else GEMINI_GAP
        clean = vdir / f"g{k:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
                        "silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
                        f"atempo={GEMINI_TEMPO},apad=pad_dur={gap}",
                        "-ar", "44100", "-ac", "1", str(clean)], check=True)
        d = _dur(clean)
        # minutage estimé sur tout le bloc (corrigé ensuite par l'alignement Whisper)
        words = _word_times(" ".join(_plain(segments[i]["text"]) for i in idx), t, t + d - gap)
        pos = 0
        for i in idx:
            n = len(_plain(segments[i]["text"]).split())
            ws = words[pos:pos + n] or [{"w": "", "start": round(t, 3), "end": round(t, 3)}]
            pos += n
            timeline.append({"index": i, "start": ws[0]["start"], "end": ws[-1]["end"],
                             "slot_end": ws[-1]["end"], "text": _plain(segments[i]["text"]), "words": ws})
        files.append(clean)
        t += d
    result = {"engine": "gemini", "path": "", "duration": round(t, 3), "timeline": timeline,
              "gemini_voice": GEMINI_VOICE, "gemini_calls": len(parts)}
    reslot(result)
    lst = vdir / "list.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files))
    voice = workdir / "voice.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(voice)], check=True, cwd=vdir)
    result["path"] = str(voice)
    return result


def reslot(voice: dict) -> dict:
    """Voix Gemini (un seul fichier pour tout le texte) : après l'alignement, chaque segment
    occupe l'écran jusqu'au début réel du suivant ; le dernier jusqu'à la fin de la voix."""
    tl = voice["timeline"]
    for k, seg in enumerate(tl):
        nxt = tl[k + 1]["start"] if k + 1 < len(tl) else voice["duration"]
        seg["slot_end"] = round(max(seg["end"], nxt), 3)
    return voice


# ------------------------------------------------------------------ Piper
def _piper_model() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    onnx = CACHE / f"{PIPER_VOICE}.onnx"
    if not onnx.exists():
        tgz = CACHE / "piper_voice.tar.gz"
        subprocess.run(["curl", "-sL", "--fail", "-o", str(tgz), PIPER_URL], check=True)
        subprocess.run(["tar", "xzf", str(tgz), "-C", str(CACHE)], check=True)
    return onnx


_PIPER = None


def _tts_piper(sent: str, out: Path, tone: str) -> None:
    global _PIPER
    from piper import PiperVoice  # type: ignore
    from piper.config import SynthesisConfig  # type: ignore
    if _PIPER is None:
        _PIPER = PiperVoice.load(str(_piper_model()))
    speed = TONES.get(tone, TONES["pote"])[3]
    with wave.open(str(out), "wb") as wf:
        _PIPER.synthesize_wav(sent, wf, syn_config=SynthesisConfig(length_scale=speed))


def release() -> None:
    """Libère le modèle de voix (plusieurs Go) avant le montage Remotion."""
    global _CB, _PIPER, _KYU
    _CB, _PIPER, _KYU = None, None, None
    _CONDS.clear()
    import gc
    gc.collect()
    try:
        import torch  # type: ignore
        torch.set_num_threads(1)
    except Exception:
        pass


# ------------------------------------------------------------------ public
FALLBACKS: list[str] = []  # moteurs abandonnés pendant ce rendu (raison), recopié dans voice.json


def engine() -> str:
    forced = os.environ.get("TF_VOICE")
    flag = Path("/tmp/tf-voice-engine")
    if not forced and flag.exists():
        forced = flag.read_text().strip()
    if forced:
        return forced
    if _fish_key():
        return "fish"
    if not VOICE_REF.exists():
        return "piper"
    try:
        import chatterbox  # noqa: F401  # type: ignore
        return "clone"
    except Exception:
        return "piper"


def _word_times(sent: str, start: float, end: float) -> list[dict]:
    """Répartit la durée d'une phrase sur ses mots (poids = longueur + pause de ponctuation)."""
    words = _plain(sent).split()
    weights = [len(re.sub(r"\W", "", w)) + 1.5 + (2.5 if re.search(r"[.,!?…:;]$", w) else 0)
               for w in words]
    tot = sum(weights) or 1
    out, t = [], start
    for w, wt in zip(words, weights):
        d = (end - start) * wt / tot
        out.append({"w": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return out


def synthesize(segments: list[dict], workdir: Path, tone: str, lead: float = 0.0) -> dict:
    """Synthétise phrase par phrase, renvoie la timeline segments + mots.
    lead : silence avant la 1re phrase (laisse l'affiche de couverture respirer)."""
    vdir = workdir / "voice"
    vdir.mkdir(parents=True, exist_ok=True)
    eng = engine()
    if eng == "gemini":
        try:
            result = _synthesize_gemini(segments, workdir, lead)
            (workdir / "voice.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
            return result
        except Exception as exc:  # secours : tout est refait avec une autre voix (pas de mélange)
            if os.environ.get("TF_VOICE_ONLY") == "gemini":  # @iafortous : pas de voix de secours
                raise RuntimeError(f"voix Gemini en échec : {exc}")
            alt = "kyutai" if KYUTAI_OK.exists() else ("fish" if _fish_key() else "piper")
            print(f"[voice] gemini a échoué ({exc}), reprise complète avec {alt}")
            FALLBACKS.append(f"gemini -> {alt} : {exc}"[:500])
            os.environ["TF_VOICE"] = alt
            return synthesize(segments, workdir, tone, lead)
    timeline, files, t, n = [], [], 0.0, 0
    if lead > 0:
        sil = vdir / "lead.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-t", f"{lead:.2f}", str(sil)], check=True)
        files.append(sil)
        t = _dur(sil)
    for i, seg in enumerate(segments):
        stone = seg.get("tone", tone)
        tempo = 1.0 if eng == "fish" else KYUTAI_TEMPO if eng == "kyutai" else TONES.get(stone, TONES["pote"])[2]
        seg_start, words = t, []
        # Fish : un appel par segment (contexte complet) avec mise en scène automatique ;
        # moteurs locaux : phrase par phrase
        sents = [direct(seg["text"], seg.get("emphasis"), stone)] if eng == "fish" else _sentences(seg["text"])
        for j, sent in enumerate(sents):
            raw = vdir / f"s{n:03d}_raw.wav"
            try:
                if eng == "kyutai":
                    _tts_kyutai(_plain(sent), raw, stone)
                elif eng == "fish":
                    _tts_fish(sent, raw, stone)
                elif eng == "clone":
                    _tts_chatterbox(_plain(sent), raw, stone)
                else:
                    _tts_piper(_plain(sent), raw, stone)
            except Exception as exc:  # secours automatique
                if eng == "kyutai":  # on recommence tout avec un autre moteur (pas de voix mélangées)
                    alt = "fish" if _fish_key() else "piper"
                    print(f"[voice] kyutai a échoué ({exc}), reprise complète avec {alt}")
                    FALLBACKS.append(f"kyutai -> {alt} : {exc}"[:300])
                    os.environ["TF_VOICE"] = alt
                    release()
                    return synthesize(segments, workdir, tone, lead)
                print(f"[voice] {eng} a échoué ({exc}), passage sur Piper")
                eng = "piper"
                _tts_piper(_plain(sent), raw, stone)
            last_of_seg = j == len(sents) - 1
            g_sent, g_seg = GAPS.get(eng, (GAP_SENT, GAP_SEG))
            gap = (g_seg if i < len(segments) - 1 else 0.7) if last_of_seg else g_sent
            gap = float(seg.get("pause_after", gap)) if last_of_seg else gap
            clean = vdir / f"s{n:03d}.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
                            "silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
                            "silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
                            f"atempo={tempo},apad=pad_dur={gap}",
                            "-ar", "44100", "-ac", "1", str(clean)], check=True)
            d = _dur(clean)
            words += _word_times(sent, t, t + d - gap)
            files.append(clean)
            t += d
            n += 1
        timeline.append({"index": i, "start": round(seg_start, 3), "end": round(words[-1]["end"], 3),
                         "slot_end": round(t, 3), "text": _plain(seg["text"]), "words": words})
    lst = vdir / "list.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files))
    voice = workdir / "voice.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(voice)], check=True, cwd=vdir)
    release()
    result = {"engine": eng, "path": str(voice), "duration": round(t, 3), "timeline": timeline}
    if FALLBACKS:
        result["fallback"] = " | ".join(FALLBACKS)
    (workdir / "voice.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return result
