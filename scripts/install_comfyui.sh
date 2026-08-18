#!/usr/bin/env bash
# Optional helper: clone and prepare a local ComfyUI instance next to the
# project so MusiGen can talk to it. Skips if the directory already exists.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -d ComfyUI ]]; then
  echo "ComfyUI/ already present — skipping clone."
else
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git
fi

pushd ComfyUI >/dev/null
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
# CPU torch by default. For CUDA, install the right wheel manually.
python -m pip install torch torchvision torchaudio
python -m pip install -r requirements.txt

# Install the ComfyUI-GGUF custom node (required for the MiniMax GGUF)
mkdir -p custom_nodes
if [[ ! -d custom_nodes/ComfyUI-GGUF ]]; then
  git clone --depth 1 https://github.com/city96/ComfyUI-GGUF.git custom_nodes/ComfyUI-GGUF
  python -m pip install -r custom_nodes/ComfyUI-GGUF/requirements.txt || true
fi

# If the MiniMax music custom node exists in your setup, drop the git clone
# line here. As of writing the node lives inside forks or the ComfyUI-GGUF
# extension itself; users may need to install a workflow-specific node.

# Link Models/ so we don't duplicate weights
mkdir -p models/diffusion_models models/text_encoders models/vae
ln -sfn "$(pwd)/../Models/music" models/musigen-music
popd >/dev/null

echo "✔ ComfyUI is ready at ./ComfyUI"
echo "  start it with:  cd ComfyUI && source .venv/bin/activate && python main.py --listen 127.0.0.1 --port 8188"
