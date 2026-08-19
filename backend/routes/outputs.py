from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import settings
from ..storage import audio_path_for, delete_record, list_records, load_record

router = APIRouter(prefix="/api/outputs", tags=["outputs"])


@router.get("")
def list_outputs(limit: int = 200) -> dict:
    recs = list_records(limit=limit)
    return {"outputs": [r.to_dict() for r in recs]}


@router.get("/{record_id}")
def get_output(record_id: str) -> dict:
    rec = load_record(record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    return rec.to_dict()


_AUDIO_MIME = {
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".opus": "audio/ogg",
    ".m4a": "audio/mp4",
}


def _mime_for(path) -> str:
    return _AUDIO_MIME.get(path.suffix.lower(), "application/octet-stream")


@router.get("/{record_id}/audio")
def get_audio(record_id: str):
    p = audio_path_for(record_id)
    if not p or not p.exists():
        # fall back to recorded path
        rec = load_record(record_id)
        if rec and rec.audio_path:
            abs_path = settings.root / rec.audio_path
            if abs_path.exists():
                return FileResponse(
                    str(abs_path),
                    media_type=_mime_for(abs_path),
                    filename=abs_path.name,
                )
        raise HTTPException(status_code=404, detail="audio not found")
    return FileResponse(str(p), media_type=_mime_for(p), filename=p.name)


@router.delete("/{record_id}")
def remove(record_id: str) -> dict:
    ok = delete_record(record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"deleted": record_id}
