"""Music generation engines.

Three implementations:
  * ComfyEngine    — submits a workflow to a running ComfyUI instance and
                     downloads the resulting .wav (MiniMax-Music3 GGUF path)
  * MusicGenEngine — Meta's MusicGen via HuggingFace transformers; works on
                     CPU/MPS/CUDA out of the box, makes real beats
  * StubEngine     — synthesises a placeholder tone locally so the UI works
                     end-to-end even without any music model

`select_engine()` picks one based on config + reachability.
"""
from __future__ import annotations

import asyncio
import functools
import json
import math
import random
import struct
import threading
import time
import uuid
import wave
from pathlib import Path
from typing import Any, AsyncIterator, Callable

import httpx

from ..config import settings
from ..storage import GenerationRecord, save_record
from .comfy_workflow import build_workflow, discover_model_files


ProgressCb = Callable[[dict[str, Any]], None]


class MusicEngineError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Stub engine
# ---------------------------------------------------------------------------


class StubEngine:
    name = "stub"

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": True,
            "placeholder": True,
            "note": (
                "STUB MODE — output is a synthesised placeholder chord, NOT "
                "real music. Install a real engine to get actual beats: "
                "run ./scripts/download_musicgen.sh (quick, Meta MusicGen) "
                "or ./scripts/install_comfyui.sh + download_music_model.sh "
                "(full, MiniMax-Music3)."
            ),
        }

    async def generate(
        self, rec: GenerationRecord, progress: ProgressCb | None = None
    ) -> GenerationRecord:
        rec.engine = self.name
        rec.status = "running"
        save_record(rec)
        duration = float(rec.params.get("duration", 8.0))
        seed = int(rec.params.get("seed", random.randint(1, 2**31 - 1)))

        # Emit fake progress
        steps = 12
        for i in range(steps):
            await asyncio.sleep(min(0.15, duration / steps / 4))
            if progress:
                progress(
                    {
                        "type": "progress",
                        "value": (i + 1) / steps,
                        "message": f"synthesising stub audio ({i + 1}/{steps})",
                    }
                )

        out = Path(settings.outputs_dir) / rec.id / f"{rec.id}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        _synthesise_placeholder(out, duration_s=duration, seed=seed, prompt=rec.prompt)

        rec.audio_path = str(out.relative_to(settings.root))
        rec.duration_s = duration
        rec.status = "done"
        save_record(rec)
        return rec


def _synthesise_placeholder(path: Path, *, duration_s: float, seed: int, prompt: str) -> None:
    """A tiny stereo WAV: a slowly evolving chord seeded by the prompt hash."""
    rng = random.Random(seed ^ (hash(prompt) & 0xFFFFFFFF))
    sr = 32000
    n = int(sr * duration_s)
    root_hz = rng.choice([164.81, 196.00, 220.00, 246.94, 293.66])  # E3..D4
    intervals = [1.0, 1.25, 1.5]  # major triad ratios
    partials = [(root_hz * i, 1.0 / (k + 1)) for k, i in enumerate(intervals)]
    detune = [rng.uniform(-0.4, 0.4) for _ in partials]

    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        two_pi = 2 * math.pi
        frames = bytearray()
        for k in range(n):
            t = k / sr
            env = min(1.0, t * 2) * min(1.0, (duration_s - t) * 2)
            env = max(env, 0.0)
            s = 0.0
            for (freq, amp), d in zip(partials, detune):
                s += amp * math.sin(two_pi * (freq + d) * t)
            s += 0.05 * math.sin(two_pi * root_hz * 0.5 * t)  # sub
            s *= 0.22 * env
            left = int(max(-1.0, min(1.0, s)) * 32767)
            right = int(max(-1.0, min(1.0, s * 0.98)) * 32767)
            frames += struct.pack("<hh", left, right)
        w.writeframes(bytes(frames))


# ---------------------------------------------------------------------------
# MusicGen engine (Meta MusicGen via HuggingFace transformers)
# ---------------------------------------------------------------------------


class MusicGenEngine:
    """Real text-to-music via transformers + Meta's MusicGen.

    Loads on first generate() call (heavy) and keeps the model in memory.
    Works on CPU, Apple MPS, and CUDA. The 'small' 300M-param model is
    plenty for beats; users can override with MUSIGEN_MUSICGEN_MODEL.
    """

    name = "musicgen"

    _default_id = "facebook/musicgen-small"

    def __init__(self, model_id: str | None = None) -> None:
        import os

        self.model_id = model_id or os.getenv(
            "MUSIGEN_MUSICGEN_MODEL", self._default_id
        )
        self._model: Any = None
        self._processor: Any = None
        self._device: str | None = None
        self._sample_rate: int | None = None
        self._lock = threading.Lock()
        self._load_error: str | None = None

    # ---- status

    def status(self) -> dict[str, Any]:
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401
            deps_ok = True
            deps_note = None
        except Exception as e:
            deps_ok = False
            deps_note = f"install with: pip install -r requirements-musicgen.txt ({e})"

        return {
            "name": self.name,
            "available": deps_ok,
            "loaded": self._model is not None,
            "model_id": self.model_id,
            "device": self._device,
            "sample_rate": self._sample_rate,
            "deps_ok": deps_ok,
            "deps_note": deps_note,
            "load_error": self._load_error,
        }

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoProcessor, MusicgenForConditionalGeneration
        except Exception as e:
            self._load_error = (
                f"MusicGen deps not installed: {e}. "
                "Run: pip install -r requirements-musicgen.txt"
            )
            raise MusicEngineError(self._load_error)

        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        try:
            self._processor = AutoProcessor.from_pretrained(self.model_id)
            self._model = MusicgenForConditionalGeneration.from_pretrained(self.model_id)
            self._model.to(device)
            self._model.eval()
            self._device = device
            self._sample_rate = self._model.config.audio_encoder.sampling_rate
            self._load_error = None
        except Exception as e:
            self._load_error = f"MusicGen model load failed: {e}"
            self._model = None
            self._processor = None
            raise MusicEngineError(self._load_error)

    # ---- generate

    async def generate(
        self, rec: GenerationRecord, progress: ProgressCb | None = None
    ) -> GenerationRecord:
        rec.engine = self.name
        rec.status = "running"
        save_record(rec)

        if progress:
            progress({"type": "progress", "value": 0.02, "message": "loading MusicGen (first run downloads weights)"})

        # Load + generate off the event loop
        loop = asyncio.get_running_loop()
        try:
            audio_np, sr = await loop.run_in_executor(
                None,
                functools.partial(self._generate_blocking, rec, progress),
            )
        except MusicEngineError:
            raise
        except Exception as e:
            raise MusicEngineError(f"MusicGen generation failed: {e}") from e

        out = Path(settings.outputs_dir) / rec.id / f"{rec.id}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        _write_wav_from_float(out, audio_np, sr)

        rec.audio_path = str(out.relative_to(settings.root))
        rec.duration_s = float(rec.params.get("duration", 8.0))
        rec.status = "done"
        save_record(rec)
        return rec

    def _generate_blocking(
        self, rec: GenerationRecord, progress: ProgressCb | None
    ):
        with self._lock:
            self._load()
            import torch

            duration = float(rec.params.get("duration", 8.0))
            # MusicGen produces at ~50 tokens/sec of audio. Cap to 30s to
            # keep CPU users happy; longer for GPU is fine.
            max_new_tokens = max(64, int(duration * 50))

            prompt = rec.prompt.strip() or "melodic instrumental music"
            if progress:
                progress({"type": "progress", "value": 0.08, "message": f"encoding prompt ({self._device})"})

            inputs = self._processor(
                text=[prompt],
                padding=True,
                return_tensors="pt",
            ).to(self._device)

            seed = rec.params.get("seed")
            if seed is not None:
                torch.manual_seed(int(seed))

            # Progress callback via TextStreamer isn't well-supported for
            # MusicGen; emit coarse fake progress from a timer thread while
            # the generate call runs.
            stop_progress = threading.Event()

            def tick() -> None:
                start = time.time()
                # Assume ~duration*3 seconds on CPU for the whole thing
                est = max(6.0, duration * 3.0)
                while not stop_progress.wait(0.4):
                    elapsed = time.time() - start
                    frac = min(0.9, 0.15 + (elapsed / est) * 0.75)
                    if progress:
                        progress({"type": "progress", "value": frac, "message": f"generating on {self._device}…"})

            t = threading.Thread(target=tick, daemon=True)
            t.start()
            try:
                with torch.no_grad():
                    audio = self._model.generate(
                        **inputs,
                        do_sample=True,
                        guidance_scale=float(rec.params.get("cfg", 3.0)),
                        max_new_tokens=max_new_tokens,
                        temperature=float(rec.params.get("temperature", 1.0)),
                    )
            finally:
                stop_progress.set()
                t.join(timeout=1)

            if progress:
                progress({"type": "progress", "value": 0.98, "message": "encoding wav"})

            audio_np = audio[0, 0].to("cpu").float().numpy()
            return audio_np, self._sample_rate


def _write_wav_from_float(path: Path, audio, sr: int) -> None:
    """Write a mono float32 numpy array to a 16-bit PCM WAV."""
    import struct as _s

    # Clamp and convert to int16
    peak = float(max(1e-9, abs(audio).max()))
    if peak > 1.0:
        audio = audio / peak
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        buf = bytearray()
        for sample in audio:
            v = int(max(-1.0, min(1.0, float(sample))) * 32767)
            buf += _s.pack("<h", v)
        w.writeframes(bytes(buf))


# ---------------------------------------------------------------------------
# ComfyUI engine
# ---------------------------------------------------------------------------


class ComfyEngine:
    name = "comfy"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.comfy_url).rstrip("/")
        self.client_id = uuid.uuid4().hex

    def status(self) -> dict[str, Any]:
        reachable = False
        detail = None
        try:
            with httpx.Client(timeout=1.5) as c:
                r = c.get(f"{self.base_url}/system_stats")
                reachable = r.status_code == 200
                if reachable:
                    detail = r.json()
        except Exception as e:
            detail = str(e)
        files = discover_model_files()
        return {
            "name": self.name,
            "available": reachable and all(files.values()),
            "reachable": reachable,
            "base_url": self.base_url,
            "detail": detail,
            "model_files": files,
        }

    async def generate(
        self, rec: GenerationRecord, progress: ProgressCb | None = None
    ) -> GenerationRecord:
        rec.engine = self.name
        rec.status = "running"
        save_record(rec)

        files = discover_model_files()
        missing = [k for k, v in files.items() if not v]
        if missing:
            raise MusicEngineError(
                f"ComfyUI engine missing model files: {', '.join(missing)}. "
                "Drop them into Models/music/ (see scripts/download_music_model.sh)."
            )

        params = rec.params
        workflow = build_workflow(
            lyrics=rec.lyrics,
            description=rec.prompt,
            duration_s=float(params.get("duration", 30.0)),
            seed=int(params.get("seed", random.randint(1, 2**31 - 1))),
            steps=int(params.get("steps", 30)),
            cfg=float(params.get("cfg", 4.0)),
            sampler_name=params.get("sampler", "euler"),
            scheduler=params.get("scheduler", "normal"),
            music_ckpt=files["music_ckpt"],  # type: ignore[arg-type]
            text_encoder=files["text_encoder"],  # type: ignore[arg-type]
            vae=files["vae"],  # type: ignore[arg-type]
            output_prefix=f"musigen/{rec.id}",
        )

        prompt_id = await self._queue(workflow)
        outputs = await self._wait(prompt_id, progress=progress)

        audio_info = self._first_audio(outputs)
        if not audio_info:
            raise MusicEngineError("ComfyUI produced no audio output")

        out_dir = Path(settings.outputs_dir) / rec.id
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{rec.id}.wav"
        await self._download(audio_info, target)

        rec.audio_path = str(target.relative_to(settings.root))
        rec.duration_s = float(params.get("duration", 30.0))
        rec.status = "done"
        save_record(rec)
        return rec

    # ---- HTTP + WS helpers

    async def _queue(self, workflow: dict[str, Any]) -> str:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow, "client_id": self.client_id},
            )
            r.raise_for_status()
            data = r.json()
            return data["prompt_id"]

    async def _wait(
        self, prompt_id: str, progress: ProgressCb | None
    ) -> dict[str, Any]:
        import websockets

        ws_url = self.base_url.replace("http", "ws") + f"/ws?clientId={self.client_id}"
        async with websockets.connect(ws_url, max_size=None) as ws:
            while True:
                raw = await ws.recv()
                if isinstance(raw, bytes):
                    continue
                msg = json.loads(raw)
                t = msg.get("type")
                data = msg.get("data") or {}
                if t == "progress" and progress:
                    total = data.get("max") or 1
                    progress(
                        {
                            "type": "progress",
                            "value": data.get("value", 0) / max(1, total),
                            "message": f"step {data.get('value')}/{total}",
                        }
                    )
                elif t == "executing" and progress:
                    progress(
                        {
                            "type": "node",
                            "node": data.get("node"),
                        }
                    )
                elif t == "execution_error":
                    raise MusicEngineError(
                        f"ComfyUI execution error: {data.get('exception_message')}"
                    )
                if (
                    t == "executing"
                    and data.get("node") is None
                    and data.get("prompt_id") == prompt_id
                ):
                    break

        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{self.base_url}/history/{prompt_id}")
            r.raise_for_status()
            history = r.json()
            outputs = history.get(prompt_id, {}).get("outputs", {})
            return outputs

    def _first_audio(self, outputs: dict[str, Any]) -> dict[str, Any] | None:
        for _, node_out in outputs.items():
            for key in ("audio", "audios", "files", "output"):
                items = node_out.get(key)
                if not items:
                    continue
                if isinstance(items, list) and items and isinstance(items[0], dict):
                    return items[0]
        return None

    async def _download(self, info: dict[str, Any], target: Path) -> None:
        params = {
            "filename": info.get("filename"),
            "type": info.get("type", "output"),
        }
        if info.get("subfolder"):
            params["subfolder"] = info["subfolder"]
        async with httpx.AsyncClient(timeout=None) as c:
            async with c.stream("GET", f"{self.base_url}/view", params=params) as r:
                r.raise_for_status()
                with target.open("wb") as f:
                    async for chunk in r.aiter_bytes(8192):
                        f.write(chunk)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def select_engine() -> Any:
    kind = settings.music_engine
    if kind == "stub":
        return StubEngine()
    if kind == "comfy":
        return ComfyEngine()
    if kind == "musicgen":
        return MusicGenEngine()
    # auto: prefer comfy (real MiniMax) → musicgen (real, easier) → stub
    comfy = ComfyEngine()
    if comfy.status()["available"]:
        return comfy
    mg = MusicGenEngine()
    if mg.status()["available"]:
        return mg
    return StubEngine()
