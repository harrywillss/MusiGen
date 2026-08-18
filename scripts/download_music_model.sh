#!/usr/bin/env bash
# Download the MiniMax-Music3 GGUF + companion text-encoder + VAE into
# Models/music/. Requires the `huggingface_hub` python package (installed by
# setup.sh) and a valid network connection.
set -euo pipefail
cd "$(dirname "$0")/.."

TARGET="Models/music"
mkdir -p "$TARGET"

# Default GGUF quant (change with env: QUANT=Q6_K)
QUANT="${QUANT:-Q8_0}"
REPO="${REPO:-Abiray/MiniMax-Music3-GGUF}"
GGUF_FILE="${GGUF_FILE:-MiniMax-Music3-${QUANT}.gguf}"

# Companion files usually referenced by the workflow (adjust if the upstream
# repo names them differently)
TE_REPO="${TE_REPO:-MiniMaxAI/MiniMax-Music3}"
TE_FILE="${TE_FILE:-text_encoder.safetensors}"
VAE_FILE="${VAE_FILE:-vae.safetensors}"

echo "▶ MusiGen: downloading music model"
echo "  repo:        $REPO"
echo "  gguf file:   $GGUF_FILE  (quant=$QUANT)"
echo "  te repo:     $TE_REPO"
echo "  te file:     $TE_FILE"
echo "  vae file:    $VAE_FILE"
echo "  destination: $TARGET"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 required." >&2
  exit 1
fi

python3 - <<PY
from huggingface_hub import hf_hub_download
import os, sys, shutil

target = "$TARGET"
os.makedirs(target, exist_ok=True)

def fetch(repo, filename):
    print(f"  ↓ {repo} :: {filename}")
    try:
        path = hf_hub_download(repo_id=repo, filename=filename, local_dir=target, local_dir_use_symlinks=False)
        print(f"    -> {path}")
    except Exception as e:
        print(f"    !! failed: {e}", file=sys.stderr)
        return False
    return True

ok = True
ok &= fetch("$REPO", "$GGUF_FILE")
# text encoder + vae are best-effort — different community repos name them
# differently, so failure here is not fatal
for alt in ("$TE_FILE", "text_encoder/model.safetensors", "clip/model.safetensors"):
    if fetch("$TE_REPO", alt):
        break
for alt in ("$VAE_FILE", "vae/diffusion_pytorch_model.safetensors"):
    if fetch("$TE_REPO", alt):
        break

print()
print("done." if ok else "some downloads failed — see notes above.")
PY

echo
echo "Files now in $TARGET:"
ls -lh "$TARGET"
