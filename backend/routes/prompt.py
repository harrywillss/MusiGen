from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..engines.llm_engine import LLMUnavailable, llm_engine
from ..prompts import (
    CRITIQUE_SYSTEM,
    EXPAND_SYSTEM,
    LYRICS_SYSTEM,
    STYLE_PRESETS,
    TRANSLATE_SYSTEM,
)

router = APIRouter(prefix="/api/prompt", tags=["prompt"])


class ExpandBody(BaseModel):
    idea: str = Field(..., description="Short user idea")
    style: str | None = Field(None, description="Optional preset key to steer output")
    temperature: float = 0.7


class TranslateBody(BaseModel):
    text: str
    temperature: float = 0.3


class LyricsBody(BaseModel):
    theme: str
    temperature: float = 0.9
    max_tokens: int = 400


class CritiqueBody(BaseModel):
    prompt: str
    lyrics: str | None = None
    temperature: float = 0.5


def _need_llm() -> None:
    st = llm_engine.status()
    if not st["loaded"]:
        # try to lazy-load once
        llm_engine.load()
        st = llm_engine.status()
    if not st["loaded"]:
        raise HTTPException(
            status_code=503,
            detail=st.get("error") or "No LLM loaded. Download one to Models/llm/.",
        )


@router.post("/expand")
def expand(body: ExpandBody) -> dict:
    _need_llm()
    steer = ""
    if body.style and body.style in STYLE_PRESETS:
        steer = (
            f"\n\nAnchor the description in this style reference:\n"
            f"{STYLE_PRESETS[body.style]}"
        )
    try:
        out = llm_engine.chat(
            EXPAND_SYSTEM,
            f"User idea:\n{body.idea}{steer}",
            temperature=body.temperature,
            max_tokens=300,
        )
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"prompt": out}


@router.post("/translate")
def translate(body: TranslateBody) -> dict:
    _need_llm()
    try:
        out = llm_engine.chat(
            TRANSLATE_SYSTEM,
            body.text,
            temperature=body.temperature,
            max_tokens=300,
        )
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"prompt": out}


@router.post("/lyrics")
def lyrics(body: LyricsBody) -> dict:
    _need_llm()
    try:
        out = llm_engine.chat(
            LYRICS_SYSTEM,
            body.theme,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"lyrics": out}


@router.post("/critique")
def critique(body: CritiqueBody) -> dict:
    _need_llm()
    payload = f"Prompt:\n{body.prompt}"
    if body.lyrics:
        payload += f"\n\nLyrics:\n{body.lyrics}"
    try:
        out = llm_engine.chat(
            CRITIQUE_SYSTEM,
            payload,
            temperature=body.temperature,
            max_tokens=250,
        )
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"critique": out}


@router.get("/presets")
def presets() -> dict:
    return {"presets": STYLE_PRESETS}
