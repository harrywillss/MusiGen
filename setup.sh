#!/usr/bin/env bash
# One-shot local install: creates a Python venv, installs backend deps,
# installs frontend deps, prints next steps.
set -euo pipefail
cd "$(dirname "$0")"

echo "▶ MusiGen setup"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1; then
  echo "node is required (v18+)." >&2
  exit 1
fi

# --- Python venv -----------------------------------------------------------
if [[ ! -d .venv ]]; then
  echo "  creating .venv"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools >/dev/null
echo "  installing python deps (this includes llama-cpp-python, may take a few minutes)"
python -m pip install -r requirements.txt

# --- Node deps -------------------------------------------------------------
echo "  installing frontend deps"
pushd frontend >/dev/null
npm install --no-audit --no-fund
popd >/dev/null

cat <<EOF

✔ Setup complete.

Next steps:
  1. (Optional) Download the music model:
       ./scripts/download_music_model.sh
     Env overrides:
       QUANT=Q6_K REPO=Abiray/MiniMax-Music3-GGUF GGUF_FILE=MiniMax-Music3-Q6_K.gguf ./scripts/download_music_model.sh

  2. Download the LLM copilot:
       ./scripts/download_llm.sh

  3. (Optional) Install a local ComfyUI:
       ./scripts/install_comfyui.sh
     Then start it: cd ComfyUI && source .venv/bin/activate && python main.py --listen 127.0.0.1 --port 8188

  4. Run the app:
       ./run.sh

  The web UI is at http://localhost:5173
  The API is at   http://localhost:8000
EOF
