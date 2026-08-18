from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import generate, models, outputs, prompt, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("musigen")

app = FastAPI(
    title="MusiGen",
    description="Local text-to-music playground with an LLM prompt copilot.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(prompt.router)
app.include_router(generate.router)
app.include_router(outputs.router)
app.include_router(models.router)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.on_event("startup")
def on_startup() -> None:
    log.info("MusiGen backend starting")
    log.info("Root:         %s", settings.root)
    log.info("Models dir:   %s", settings.models_dir)
    log.info("Outputs dir:  %s", settings.outputs_dir)
    log.info("Music engine: %s", settings.music_engine)
    log.info("Comfy URL:    %s", settings.comfy_url)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
