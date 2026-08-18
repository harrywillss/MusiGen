from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..engines.llm_engine import llm_engine
from ..engines.music_engine import ComfyEngine, MusicGenEngine, StubEngine, select_engine
from ..prompts import STYLE_PRESETS, preset_names

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def status() -> dict:
    engine = select_engine()
    return {
        "root": str(settings.root),
        "models_dir": str(settings.models_dir),
        "outputs_dir": str(settings.outputs_dir),
        "music_engine": engine.status(),
        "llm": llm_engine.status(),
        "config": {
            "comfy_url": settings.comfy_url,
            "music_engine_mode": settings.music_engine,
            "llm_ctx": settings.llm_ctx,
            "llm_gpu_layers": settings.llm_gpu_layers,
        },
        "presets": preset_names(),
    }


@router.get("/presets")
def presets() -> dict:
    return {"presets": STYLE_PRESETS}


class LLMLoadBody(BaseModel):
    model_path: str | None = None


@router.post("/llm/load")
def load_llm(body: LLMLoadBody) -> dict:
    llm_engine.load(body.model_path)
    st = llm_engine.status()
    if not st["loaded"]:
        raise HTTPException(status_code=400, detail=st.get("error") or "load failed")
    return st


@router.post("/llm/unload")
def unload_llm() -> dict:
    llm_engine.unload()
    return llm_engine.status()


class EngineBody(BaseModel):
    mode: str  # auto|comfy|stub


@router.post("/music/mode")
def set_music_mode(body: EngineBody) -> dict:
    if body.mode not in ("auto", "comfy", "musicgen", "stub"):
        raise HTTPException(
            status_code=400,
            detail="mode must be auto|comfy|musicgen|stub",
        )
    settings.music_engine = body.mode
    return select_engine().status()


@router.get("/engines")
def engines() -> dict:
    return {
        "current": select_engine().name,
        "modes": ["auto", "comfy", "musicgen", "stub"],
        "comfy": ComfyEngine().status(),
        "musicgen": MusicGenEngine().status(),
        "stub": StubEngine().status(),
    }
