from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _root() -> Path:
    env = os.getenv("MUSIGEN_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


ROOT = _root()


@dataclass
class Settings:
    root: Path = ROOT
    models_dir: Path = Path(os.getenv("MUSIGEN_MODELS_DIR", ROOT / "Models"))
    outputs_dir: Path = Path(os.getenv("MUSIGEN_OUTPUTS_DIR", ROOT / "Outputs"))

    # LLM
    llm_model: str | None = os.getenv("MUSIGEN_LLM_MODEL")
    llm_ctx: int = int(os.getenv("MUSIGEN_LLM_CTX", "4096"))
    llm_gpu_layers: int = int(os.getenv("MUSIGEN_LLM_GPU_LAYERS", "0"))
    llm_threads: int = int(os.getenv("MUSIGEN_LLM_THREADS", "0")) or None  # type: ignore[assignment]

    # Music
    music_engine: str = os.getenv("MUSIGEN_MUSIC_ENGINE", "auto")  # auto|comfy|musicgen|stub
    comfy_url: str = os.getenv("MUSIGEN_COMFY_URL", "http://127.0.0.1:8188")

    # Server
    host: str = os.getenv("MUSIGEN_HOST", "127.0.0.1")
    port: int = int(os.getenv("MUSIGEN_PORT", "8000"))

    # Frontend origin(s) allowed for CORS during dev
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv(
            "MUSIGEN_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
    )

    def ensure_dirs(self) -> None:
        (self.models_dir / "music").mkdir(parents=True, exist_ok=True)
        (self.models_dir / "llm").mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
