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
  1. Download the LLM copilot (for prompt expansion / lyrics):
       ./scripts/download_llm.sh

  2. Install a real music engine — pick ONE:
       a) FAST — Meta MusicGen (real music, no ComfyUI needed):
            ./scripts/download_musicgen.sh
       b) FULL — MiniMax-Music3 via ComfyUI (more setup, higher quality):
            ./scripts/download_music_model.sh
            ./scripts/install_comfyui.sh
            # then run ComfyUI on port 8188

  3. Run the app:
       ./run.sh

  If you skip step 2 entirely, the UI still works — but the audio you
  get back will be a synthesised placeholder chord, NOT real music.
  The app will show a big red banner reminding you.

  The web UI is at http://localhost:5173
  The API is at   http://localhost:8000
EOF
