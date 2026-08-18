"""Template ComfyUI workflow for MiniMax-Music3-GGUF.

We keep the workflow minimal and configurable. The exact node ids/types match
the community reference workflow used with the ComfyUI-GGUF and
ComfyUI-MiniMax-Music custom nodes; users can override this with their own
workflow JSON by dropping a file at Models/music/workflow.json.
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
) -> dict[str, Any]:
    return {
        "1": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {"unet_name": music_ckpt},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": text_encoder, "type": "minimax_music"},
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": vae},
        },
        "4": {
            "class_type": "MiniMaxMusicConditioning",
            "inputs": {
                "clip": ["2", 0],
                "lyrics": lyrics,
                "description": description,
                "duration": duration_s,
            },
        },
        "5": {
            "class_type": "MiniMaxMusicConditioning",
            "inputs": {
                "clip": ["2", 0],
                "lyrics": "",
                "description": "silence, low quality, noise, distortion",
                "duration": duration_s,
            },
        },
        "6": {
            "class_type": "EmptyMusicLatent",
            "inputs": {"duration": duration_s, "sample_rate": 32000, "batch_size": 1},
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
            "class_type": "SaveAudio",
            "inputs": {
                "audio": ["8", 0],
                "filename_prefix": output_prefix,
                "format": "wav",
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
    """Return a workflow dict, either the user's override or the default."""
    override = settings.models_dir / "music" / "workflow.json"
    if override.exists():
        raw = override.read_text()
        # allow simple string interpolation using $VAR-style tokens
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
            ["MiniMax-Music*.gguf", "*minimax_music3_dit*.safetensors", "*Music*.gguf", "*.gguf"],
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
