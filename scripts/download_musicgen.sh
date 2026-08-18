#!/usr/bin/env bash
# Pre-download Meta MusicGen weights + install the optional deps so the
# first generate() call doesn't have to wait for a 1.2 GB download.
set -euo pipefail
cd "$(dirname "$0")/.."

# Activate venv if present
if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

MODEL="${MUSIGEN_MUSICGEN_MODEL:-facebook/musicgen-small}"

echo "▶ MusiGen: installing MusicGen deps (torch + transformers)"
pip install -r requirements-musicgen.txt

echo "▶ MusiGen: pre-downloading $MODEL (cached under ~/.cache/huggingface)"
python3 - <<PY
from transformers import AutoProcessor, MusicgenForConditionalGeneration
model_id = "$MODEL"
print(f"  loading processor: {model_id}")
AutoProcessor.from_pretrained(model_id)
print(f"  loading model:     {model_id}")
MusicgenForConditionalGeneration.from_pretrained(model_id)
print("done.")
PY

echo
echo "✔ MusicGen is ready. In the app, System panel → engine → 'musicgen'"
echo "  (or leave it on 'auto' and it will pick musicgen automatically)."
