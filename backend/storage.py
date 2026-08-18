from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import settings


@dataclass
class GenerationRecord:
    id: str
    created_at: float
    prompt: str
    lyrics: str
    engine: str
    params: dict[str, Any]
    audio_path: str | None = None
    duration_s: float | None = None
    status: str = "pending"
    error: str | None = None
    expanded_prompt: str | None = None
    llm_notes: str | None = None
    tags: list[str] = field(default_factory=list)

    @property
    def audio_url(self) -> str | None:
        if not self.audio_path:
            return None
        return f"/api/outputs/{self.id}/audio"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["audio_url"] = self.audio_url
        return d


def _record_dir(record_id: str) -> Path:
    return settings.outputs_dir / record_id


def _record_meta_path(record_id: str) -> Path:
    return _record_dir(record_id) / "meta.json"


def new_id() -> str:
    return f"{int(time.time())}-{uuid.uuid4().hex[:8]}"


def save_record(rec: GenerationRecord) -> None:
    d = _record_dir(rec.id)
    d.mkdir(parents=True, exist_ok=True)
    _record_meta_path(rec.id).write_text(json.dumps(rec.to_dict(), indent=2))


def load_record(record_id: str) -> GenerationRecord | None:
    p = _record_meta_path(record_id)
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    data.pop("audio_url", None)  # derived
    return GenerationRecord(**data)


def list_records(limit: int = 200) -> list[GenerationRecord]:
    if not settings.outputs_dir.exists():
        return []
    entries = []
    for child in sorted(settings.outputs_dir.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        meta = child / "meta.json"
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text())
            data.pop("audio_url", None)
            entries.append(GenerationRecord(**data))
        except Exception:
            continue
        if len(entries) >= limit:
            break
    return entries


def delete_record(record_id: str) -> bool:
    d = _record_dir(record_id)
    if not d.exists():
        return False
    for p in sorted(d.rglob("*"), reverse=True):
        try:
            if p.is_file() or p.is_symlink():
                p.unlink()
            else:
                p.rmdir()
        except OSError:
            pass
    try:
        d.rmdir()
    except OSError:
        pass
    return True


def audio_path_for(record_id: str) -> Path | None:
    d = _record_dir(record_id)
    for ext in ("wav", "flac", "mp3", "ogg"):
        matches = sorted(d.glob(f"*.{ext}"))
        if matches:
            return matches[0]
    return None
