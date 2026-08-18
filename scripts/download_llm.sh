#!/usr/bin/env bash
# Download a small instruction-tuned LLM as GGUF into Models/llm/ for the
# prompt copilot. Defaults to Qwen2.5-3B-Instruct at Q4_K_M — small, fast,
# runs on CPU. Override via env variables.
set -euo pipefail
cd "$(dirname "$0")/.."

TARGET="Models/llm"
mkdir -p "$TARGET"

REPO="${REPO:-Qwen/Qwen2.5-3B-Instruct-GGUF}"
FILE="${FILE:-qwen2.5-3b-instruct-q4_k_m.gguf}"

echo "▶ MusiGen: downloading prompt copilot LLM"
echo "  repo:  $REPO"
echo "  file:  $FILE"
echo "  dest:  $TARGET"

python3 - <<PY
from huggingface_hub import hf_hub_download
import os

os.makedirs("$TARGET", exist_ok=True)
path = hf_hub_download(repo_id="$REPO", filename="$FILE", local_dir="$TARGET", local_dir_use_symlinks=False)
print("  -> ", path)
PY

echo
echo "Files now in $TARGET:"
ls -lh "$TARGET"
