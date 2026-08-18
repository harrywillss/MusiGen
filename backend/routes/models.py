from __future__ import annotations

from fastapi import APIRouter

from ..config import settings
from ..engines.comfy_workflow import discover_model_files

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_all() -> dict:
    music_dir = settings.models_dir / "music"
    llm_dir = settings.models_dir / "llm"
    return {
        "music": {
            "dir": str(music_dir),
            "files": [
                {"name": p.name, "size": p.stat().st_size}
                for p in sorted(music_dir.glob("*"))
                if p.is_file()
            ],
            "discovered": discover_model_files(),
        },
        "llm": {
            "dir": str(llm_dir),
            "files": [
                {"name": p.name, "size": p.stat().st_size}
                for p in sorted(llm_dir.glob("*"))
                if p.is_file()
            ],
        },
    }
