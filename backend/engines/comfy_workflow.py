"""Template ComfyUI workflow for MiniMax-Music3.

Built from the official Comfy-Org workflow_templates entry
`audio_minimax_music_3.json` (Aug 2026). The real node types are:

  * UNETLoader (safetensors) or UnetLoaderGGUF (from ComfyUI-GGUF, for .gguf)
  * CLIPLoader with type="minimax"
  * VAELoader
  * MiniMaxMusic3TextEncode         ← the caption/lyrics/seed encoder
  * ConditioningZeroOut             ← negative = zeroed positive
  * EmptyMiniMaxMusic3LatentAudio   ← empty audio latent of N seconds
  * KSampler (defaults: 30 steps, cfg 1.7, sampler euler, scheduler simple)
  * VAEDecodeAudio                  ← latent → AUDIO
  * SaveAudioAdvanced               ← writes flac/mp3 into ComfyUI/output

The MiniMax node signature (as of ComfyUI 0.33):
  inputs:  clip (CLIP), caption (STRING), lyrics (STRING),
           seed (INT), max_duration (FLOAT)
  outputs: CONDITIONING, seconds (FLOAT)

Users can drop `Models/music/workflow.json` (ComfyUI API-format JSON —
Save > "Save (API Format)" in the ComfyUI web UI) to override this template
with their own workflow; simple $VAR replacements in that file are honoured.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import settings


def _default_workflow(
    *,
    music_ckpt: str,
    text_encoder: str,
    vae: str,
    lyrics: str,
    description: str,
    duration_s: float,
    seed: int,
    steps: int,
    cfg: float,
    sampler_name: str,
    scheduler: str,
    output_prefix: str,
    save_format: str = "flac",
) -> dict[str, Any]:
    # Pick the right loader for the diffusion model based on its extension.
    # .gguf → UnetLoaderGGUF (from the ComfyUI-GGUF custom node)
    # .safetensors → UNETLoader (stock ComfyUI)
    ext = Path(music_ckpt).suffix.lower()
    loader_class = "UnetLoaderGGUF" if ext == ".gguf" else "UNETLoader"

    # The text encoder is required by MiniMaxMusic3TextEncode; the node
    # rejects an empty lyrics string on some builds so we substitute a
    # placeholder marker when the user leaves it blank.
    lyrics_input = lyrics.strip() or "[Instrumental]"

    return {
        "1": {
            "class_type": loader_class,
            "inputs": (
                {"unet_name": music_ckpt}
                if loader_class == "UnetLoaderGGUF"
                else {"unet_name": music_ckpt, "weight_dtype": "default"}
            ),
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": text_encoder,
                "type": "minimax",
                "device": "default",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": vae},
        },
        "4": {
            "class_type": "MiniMaxMusic3TextEncode",
            "inputs": {
                "clip": ["2", 0],
                "caption": description,
                "lyrics": lyrics_input,
                "seed": seed,
                "max_duration": float(duration_s),
            },
        },
        "5": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["4", 0]},
        },
        "6": {
            "class_type": "EmptyMiniMaxMusic3LatentAudio",
            "inputs": {
                "seconds": float(duration_s),
                "batch_size": 1,
            },
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": 1.0,
            },
        },
        "8": {
            "class_type": "VAEDecodeAudio",
            "inputs": {"samples": ["7", 0], "vae": ["3", 0]},
        },
        "9": {
            "class_type": "SaveAudioAdvanced",
            "inputs": {
                "audio": ["8", 0],
                "filename_prefix": output_prefix,
                "format": save_format,
            },
        },
    }


def build_workflow(
    *,
    lyrics: str,
    description: str,
    duration_s: float,
    seed: int,
    steps: int,
    cfg: float,
    sampler_name: str,
    scheduler: str,
    music_ckpt: str,
    text_encoder: str,
    vae: str,
    output_prefix: str,
) -> dict[str, Any]:
    """Return an API-format workflow dict — user override or the default."""
    override = settings.models_dir / "music" / "workflow.json"
    if override.exists():
        raw = override.read_text()
        # Allow simple string interpolation using $VAR-style tokens
        replacements = {
            "$LYRICS": json.dumps(lyrics)[1:-1],
            "$DESCRIPTION": json.dumps(description)[1:-1],
            "$DURATION": str(duration_s),
            "$SEED": str(seed),
            "$STEPS": str(steps),
            "$CFG": str(cfg),
            "$SAMPLER": sampler_name,
            "$SCHEDULER": scheduler,
            "$MUSIC_CKPT": music_ckpt,
            "$TEXT_ENCODER": text_encoder,
            "$VAE": vae,
            "$OUTPUT_PREFIX": output_prefix,
        }
        for k, v in replacements.items():
            raw = raw.replace(k, v)
        return json.loads(raw)

    return _default_workflow(
        music_ckpt=music_ckpt,
        text_encoder=text_encoder,
        vae=vae,
        lyrics=lyrics,
        description=description,
        duration_s=duration_s,
        seed=seed,
        steps=steps,
        cfg=cfg,
        sampler_name=sampler_name,
        scheduler=scheduler,
        output_prefix=output_prefix,
    )


def discover_model_files() -> dict[str, str | None]:
    """Best-effort discovery of the three files required by the workflow.

    Looks in the ComfyUI-shaped subfolders first (diffusion_models/,
    text_encoders/, vae/) and falls back to the flat Models/music/ layout
    for backwards compatibility.
    """
    music_dir = settings.models_dir / "music"

    def _pick(subdirs: list[str], patterns: list[str]) -> str | None:
        for sub in subdirs:
            base = music_dir / sub if sub else music_dir
            if not base.exists():
                continue
            for pat in patterns:
                hits = sorted(base.glob(pat))
                if hits:
                    return hits[0].name
        return None

    return {
        "music_ckpt": _pick(
            ["diffusion_models", ""],
            [
                "*minimax_music3_dit*.safetensors",
                "MiniMax-Music*.gguf",
                "*Music*.gguf",
                "*.gguf",
            ],
        ),
        "text_encoder": _pick(
            ["text_encoders", ""],
            [
                "*minimax_music3_text_encoder*.safetensors",
                "*text_encoder*.safetensors",
                "*t5*.safetensors",
                "*clip*.safetensors",
            ],
        ),
        "vae": _pick(
            ["vae", ""],
            [
                "*minimax_music3_dav*.safetensors",
                "*dav*.safetensors",
                "*vae*.safetensors",
                "*VAE*.safetensors",
            ],
        ),
    }
