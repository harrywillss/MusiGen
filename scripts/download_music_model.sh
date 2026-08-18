#!/usr/bin/env bash
# Download the MiniMax-Music3 diffusion GGUF + companion text-encoder + VAE
# into Models/music/, organised the way ComfyUI expects:
#
#   Models/music/
#     ├── diffusion_models/   MiniMax-Music3-<quant>.gguf
#     ├── text_encoders/      minimax_music3_text_encoder_bf16.safetensors
#     └── vae/                minimax_music3_dav.safetensors
#
# The diffusion GGUF comes from Abiray/MiniMax-Music3-GGUF; the text encoder
# and VAE come from Comfy-Org/MiniMax-Music-3 (the official ComfyUI repack).
set -euo pipefail
cd "$(dirname "$0")/.."

TARGET="Models/music"
mkdir -p "$TARGET/diffusion_models" "$TARGET/text_encoders" "$TARGET/vae"

# --- Diffusion GGUF (Abiray) -----------------------------------------------
QUANT="${QUANT:-Q8_0}"
GGUF_REPO="${GGUF_REPO:-Abiray/MiniMax-Music3-GGUF}"
GGUF_FILE="${GGUF_FILE:-MiniMax-Music3-${QUANT}.gguf}"

# --- Text encoder + VAE (Comfy-Org repack) ---------------------------------
# Text-encoder variants (bf16 = highest quality, pruned/int8 = smaller):
#   minimax_music3_text_encoder_bf16.safetensors             ~ full
#   minimax_music3_text_encoder_pruned_bf16.safetensors      ~ trimmed
#   minimax_music3_text_encoder_pruned_int8_convrot.safetensors  smallest
TE_REPO="${TE_REPO:-Comfy-Org/MiniMax-Music-3}"
TE_FILE="${TE_FILE:-text_encoders/minimax_music3_text_encoder_bf16.safetensors}"
VAE_FILE="${VAE_FILE:-vae/minimax_music3_dav.safetensors}"

echo "▶ MusiGen: downloading MiniMax-Music3 assets"
echo "  destination:    $TARGET"
echo "  diffusion gguf: $GGUF_REPO :: $GGUF_FILE"
echo "  text encoder:   $TE_REPO   :: $TE_FILE"
echo "  vae:            $TE_REPO   :: $VAE_FILE"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 required." >&2
  exit 1
fi

python3 - <<PY
from huggingface_hub import hf_hub_download
from pathlib import Path
import sys, shutil, os

target = Path("$TARGET")
plans = [
    ("$GGUF_REPO", "$GGUF_FILE",  target / "diffusion_models"),
    ("$TE_REPO",   "$TE_FILE",    target / "text_encoders"),
    ("$TE_REPO",   "$VAE_FILE",   target / "vae"),
]

failed = []
for repo, filename, dest in plans:
    dest.mkdir(parents=True, exist_ok=True)
    print(f"  ↓ {repo} :: {filename}")
    try:
        path = hf_hub_download(repo_id=repo, filename=filename, local_dir=str(dest))
        # hf_hub_download preserves the filename's subfolder inside local_dir
        # (e.g. text_encoders/foo.safetensors under our text_encoders/ target).
        # Flatten it so downstream code doesn't need to know.
        p = Path(path)
        if p.parent != dest:
            new = dest / p.name
            if new.exists():
                new.unlink()
            shutil.move(str(p), str(new))
            # remove now-empty intermediate dir(s)
            try:
                p.parent.rmdir()
            except OSError:
                pass
            print(f"    -> {new}")
        else:
            print(f"    -> {p}")
    except Exception as e:
        print(f"    !! failed: {e}", file=sys.stderr)
        failed.append((repo, filename))

# Migrate a legacy top-level GGUF (from earlier runs of this script) into
# diffusion_models/ so ComfyUI's folder discovery still finds it.
legacy = list(target.glob("*.gguf"))
for old in legacy:
    new = target / "diffusion_models" / old.name
    if not new.exists():
        shutil.move(str(old), str(new))
        print(f"  ↺ moved legacy {old.name} -> diffusion_models/")

# Sweep away any now-empty leftover dirs from earlier failed runs
for junk in ("text_encoder", "clip"):
    p = target / junk
    if p.exists() and p.is_dir() and not any(p.iterdir()):
        p.rmdir()

print()
if failed:
    print("Some downloads failed:", file=sys.stderr)
    for r, f in failed:
        print(f"  - {r} :: {f}", file=sys.stderr)
    sys.exit(1)
print("✔ all files downloaded")
PY

echo
echo "Files now in $TARGET:"
find "$TARGET" -type f -exec ls -lh {} +
