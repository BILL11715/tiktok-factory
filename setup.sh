#!/usr/bin/env bash
# Installation de l'environnement de rendu (environnement cloud vierge à chaque run).
# Usage : bash setup.sh   (puis lancer le rendu avec /tmp/tf-venv/bin/python)
# Écrit le moteur de voix retenu dans /tmp/tf-voice-engine (clone ou piper).
set -u
VENV=${TF_VENV:-/tmp/tf-venv}
LOG=/tmp/tf-setup.log
export HF_HUB_DISABLE_XET=1
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
. "$VENV/bin/activate"
pip install -q --upgrade pip >>"$LOG" 2>&1
pip install -q requests pillow "numpy<2.4" piper-tts pyyaml faster-whisper >>"$LOG" 2>&1 || echo "[setup] ERREUR pip base (voir $LOG)"
# Modèle d'alignement mot par mot (synchro image/son), téléchargé une fois
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" >>"$LOG" 2>&1 \
  && echo "[setup] alignement mot par mot prêt" || echo "[setup] alignement indisponible (temps estimés)"

# Voix Fish Audio (API) : clé en variable FISH_API_KEY ou en "API credential" de l'environnement
# (le proxy l'ajoute tout seul). Test gratuit : solde de crédits API.
# clé déposée par l'agent dans /tmp/tf-fish-key (jamais commitée)
if [ -z "${FISH_API_KEY:-}" ] && [ -s /tmp/tf-fish-key ]; then FISH_API_KEY=$(cat /tmp/tf-fish-key); fi
if [ -n "${FISH_API_KEY:-}" ]; then
  FISH_CODE=$(curl -s -o /dev/null -m 15 -w "%{http_code}" -H "Authorization: Bearer $FISH_API_KEY" https://api.fish.audio/wallet/self/api-credit)
else
  FISH_CODE=$(curl -s -o /dev/null -m 15 -w "%{http_code}" https://api.fish.audio/wallet/self/api-credit)
fi
if [ "${TF_VOICE:-}" = "fish" ] || [ "$FISH_CODE" = "200" ]; then
  echo fish > /tmp/tf-voice-engine
  echo "[setup] voix Fish Audio (API, test $FISH_CODE), secours Piper"
# Voix clonée locale : seulement si HuggingFace (CDN) est joignable
elif curl -s -o /dev/null -m 10 -w "%{http_code}" -L "https://huggingface.co/ResembleAI/chatterbox/resolve/main/conds.pt" | grep -q 200; then
  echo "[setup] HuggingFace OK, installation du clone de voix (quelques minutes)"
  pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu >>"$LOG" 2>&1 \
    || echo "[setup] torch CPU indisponible, version PyPI (plus lourde)"
  pip install -q chatterbox-tts >>"$LOG" 2>&1 && pip install -q "numpy<2.4" >>"$LOG" 2>&1
  python - <<'EOF' >>"$LOG" 2>&1 && { echo "[setup] modèle de voix prêt"; echo clone > /tmp/tf-voice-engine; } || { echo "[setup] modèle indisponible -> Piper"; echo piper > /tmp/tf-voice-engine; }
from huggingface_hub import snapshot_download
snapshot_download("ResembleAI/chatterbox", allow_patterns=["ve.pt", "t3_mtl23ls_v2.safetensors", "s3gen.pt",
                  "grapheme_mtl_merged_expanded_v1.json", "conds.pt", "Cangjie5_TC.json"])
EOF
else
  echo "[setup] HuggingFace CDN bloqué -> voix de secours Piper"
  echo piper > /tmp/tf-voice-engine
fi
# Moteur de montage Remotion (OpenMontage) : dépendances Node
( cd "$(dirname "$0")/remotion" && npm ci --no-audit --no-fund --loglevel=error >>"$LOG" 2>&1 ) \
  && echo "[setup] Remotion prêt" || echo "[setup] Remotion indisponible -> montage FFmpeg de secours"
python -c "import requests, PIL; print('[setup] OK')"
