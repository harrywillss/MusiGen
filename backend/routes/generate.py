from __future__ import annotations

import asyncio
import json
import random
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..engines.music_engine import MusicEngineError, select_engine
from ..storage import GenerationRecord, new_id, save_record

router = APIRouter(prefix="/api/generate", tags=["generate"])


class GenerateBody(BaseModel):
    prompt: str = Field(..., description="Music description")
    lyrics: str = ""
    duration: float = 30.0
    steps: int = 30
    cfg: float = 1.7   # MiniMax-Music-3 sweet spot per the official workflow
    seed: int | None = None
    sampler: str = "euler"
    scheduler: str = "simple"
    tags: list[str] = []
    expanded_prompt: str | None = None
    llm_notes: str | None = None


def _record_from_body(body: GenerateBody) -> GenerationRecord:
    import time

    seed = body.seed if body.seed is not None else random.randint(1, 2**31 - 1)
    return GenerationRecord(
        id=new_id(),
        created_at=time.time(),
        prompt=body.prompt,
        lyrics=body.lyrics,
        engine="pending",
        params={
            "duration": body.duration,
            "steps": body.steps,
            "cfg": body.cfg,
            "seed": seed,
            "sampler": body.sampler,
            "scheduler": body.scheduler,
        },
        expanded_prompt=body.expanded_prompt,
        llm_notes=body.llm_notes,
        tags=body.tags,
    )


@router.post("")
async def generate(body: GenerateBody) -> dict:
    rec = _record_from_body(body)
    save_record(rec)
    engine = select_engine()
    try:
        rec = await engine.generate(rec)
    except MusicEngineError as e:
        rec.status = "failed"
        rec.error = str(e)
        save_record(rec)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        rec.status = "failed"
        rec.error = repr(e)
        save_record(rec)
        raise HTTPException(status_code=500, detail=repr(e))
    return rec.to_dict()


@router.websocket("/ws")
async def generate_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        raw = await ws.receive_text()
        payload = json.loads(raw)
        body = GenerateBody(**payload)
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"bad body: {e}"})
        await ws.close()
        return

    rec = _record_from_body(body)
    save_record(rec)
    await ws.send_json({"type": "queued", "record": rec.to_dict()})

    engine = select_engine()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def on_progress(evt: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, evt)

    async def pump() -> None:
        while True:
            evt = await queue.get()
            try:
                await ws.send_json(evt)
            except Exception:
                return

    pump_task = asyncio.create_task(pump())
    try:
        rec = await engine.generate(rec, progress=on_progress)
        await ws.send_json({"type": "done", "record": rec.to_dict()})
    except MusicEngineError as e:
        rec.status = "failed"
        rec.error = str(e)
        save_record(rec)
        await ws.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        rec.status = "failed"
        rec.error = repr(e)
        save_record(rec)
        try:
            await ws.send_json({"type": "error", "message": repr(e)})
        except Exception:
            pass
    finally:
        pump_task.cancel()
        try:
            await ws.close()
        except Exception:
            pass
