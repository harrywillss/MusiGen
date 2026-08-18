"""Small wrapper around llama-cpp-python for the prompt copilot.

Loads lazily so the API server starts even without an LLM installed;
the /system status endpoint tells the UI whether the copilot is live."""
from __future__ import annotations

import glob
import os
import threading
from pathlib import Path
from typing import Any

from ..config import settings


class LLMUnavailable(RuntimeError):
    """Raised when a copilot call is attempted but no LLM is loaded."""


def _find_default_llm() -> str | None:
    if settings.llm_model:
        p = Path(settings.llm_model)
        if p.exists():
            return str(p)
    llm_dir = settings.models_dir / "llm"
    if not llm_dir.exists():
        return None
    candidates = sorted(glob.glob(str(llm_dir / "*.gguf")))
    # Prefer instruct/chat models when multiple files present
    for c in candidates:
        low = c.lower()
        if "instruct" in low or "chat" in low or "it" in low:
            return c
    return candidates[0] if candidates else None


class LLMEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._llama: Any = None
        self._model_path: str | None = None
        self._load_error: str | None = None
        self._tried_load = False

    # ---- public

    @property
    def model_path(self) -> str | None:
        return self._model_path

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self._llama is not None,
            "model_path": self._model_path,
            "error": self._load_error,
            "available_models": self._available_models(),
            "ctx": settings.llm_ctx,
            "gpu_layers": settings.llm_gpu_layers,
        }

    def load(self, model_path: str | None = None) -> None:
        with self._lock:
            self._tried_load = True
            path = model_path or _find_default_llm()
            if not path:
                self._load_error = "No LLM .gguf found in Models/llm/"
                self._llama = None
                self._model_path = None
                return
            if self._llama is not None and self._model_path == path:
                return
            try:
                from llama_cpp import Llama  # type: ignore
            except Exception as e:  # pragma: no cover - install-time issue
                self._load_error = f"llama-cpp-python not installed: {e}"
                self._llama = None
                return
            try:
                kwargs: dict[str, Any] = dict(
                    model_path=path,
                    n_ctx=settings.llm_ctx,
                    n_gpu_layers=settings.llm_gpu_layers,
                    verbose=False,
                )
                if settings.llm_threads:
                    kwargs["n_threads"] = settings.llm_threads
                self._llama = Llama(**kwargs)
                self._model_path = path
                self._load_error = None
            except Exception as e:
                self._llama = None
                self._model_path = None
                self._load_error = f"Failed to load LLM: {e}"

    def unload(self) -> None:
        with self._lock:
            self._llama = None
            self._model_path = None

    def chat(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> str:
        if not self._tried_load:
            self.load()
        if self._llama is None:
            raise LLMUnavailable(self._load_error or "LLM not loaded")
        with self._lock:
            try:
                res = self._llama.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop or [],
                )
                return res["choices"][0]["message"]["content"].strip()
            except Exception as e:
                # Some GGUFs don't ship a chat template — fall back to a raw
                # completion in a simple Alpaca-style shape.
                prompt = (
                    f"### System\n{system}\n\n### Instruction\n{user}\n\n### Response\n"
                )
                res = self._llama.create_completion(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop or ["### Instruction", "### System"],
                )
                text = res["choices"][0]["text"].strip()
                if not text:
                    raise LLMUnavailable(f"LLM produced empty output: {e}")
                return text

    # ---- helpers

    def _available_models(self) -> list[str]:
        llm_dir = settings.models_dir / "llm"
        if not llm_dir.exists():
            return []
        return sorted(str(p.name) for p in llm_dir.glob("*.gguf"))


llm_engine = LLMEngine()
