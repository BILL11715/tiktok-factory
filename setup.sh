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
pip install -q requests pillow "numpy<2.4" piper-tts pyyaml >>"$LOG" 2>&1 || echo "[setup] ERREUR pip base (voir $LOG)"

# Voix clonée : seulement si HuggingFace (CDN) est joignable
if curl -s -o /dev/null -m 10 -w "%{http_code}" -L "https://huggingface.co/ResembleAI/chatterbox/resolve/main/conds.pt" | grep -q 200; then
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
python -c "import requests, PIL; print('[setup] OK')"
