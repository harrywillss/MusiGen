# MusiGen

A local, all-in-one interface for testing text-to-music generation models.
Runs the [MiniMax-Music3-GGUF](https://huggingface.co/Abiray/MiniMax-Music3-GGUF)
diffusion model through ComfyUI, with a small local LLM (via
`llama-cpp-python`) acting as an on-board prompt copilot that expands,
translates and restyles your ideas into the kind of dense, musically
literate descriptions these models actually respond to.

Wrapped in a retro pixel-art web UI you drive from the browser.

```
                 ┌───────────────────────┐
                 │   React (Vite)  UI    │
                 │   pixel-art studio    │
                 └──────────┬────────────┘
                            │  REST + WS
                 ┌──────────▼────────────┐
                 │   FastAPI backend     │
                 │  ┌──────────────────┐ │
                 │  │  LLM engine      │ │  ← llama-cpp-python + local GGUF
                 │  │  prompt copilot  │ │
                 │  └──────────────────┘ │
                 │  ┌──────────────────┐ │
                 │  │  Music engine    │ │  ← ComfyUI adapter / stub
                 │  └──────────────────┘ │
                 └──────────┬────────────┘
                            │
                 ┌──────────▼────────────┐
                 │   Local ComfyUI       │  ← MiniMax-Music3-GGUF
                 │   (headless, API)     │     + text encoder + VAE
                 └───────────────────────┘
```

## Features

- **Text-to-music** with lyrics + description, driven by MiniMax-Music3-GGUF
- **Prompt copilot** — a local LLM expands short ideas into rich musical
  descriptions (genre, instrumentation, tempo, mood, mixing cues)
- **Prompt translator** — turn a foreign-language idea into an
  English music description
- **Style presets** — one-click seeds: cinematic, lo-fi, drill, drum-and-bass,
  synthwave, orchestral, etc.
- **Lyrics writer** — generate lyrics on a theme, or expand a hook
- **Local model store** — everything under `Models/`
- **Output history** — every generation saved under `Outputs/` with the
  prompt, lyrics, params and audio; browseable in the UI
- **Stub mode** — the backend runs even before you download the music model,
  so you can drive the UI end-to-end and test the LLM copilot standalone
- **Pixel-art UI** — bright synthwave palette, chunky pixel type, animated
  city skyline

## Directory layout

```
MusiGen/
├── backend/            FastAPI service
├── frontend/           React + Vite web app
├── Models/
│   ├── music/          MiniMax GGUF + text_encoder + VAE
│   └── llm/            LLM GGUF for the prompt copilot
├── Outputs/            Generated .wav files + metadata JSON
├── scripts/            Setup + model download helpers
├── setup.sh            One-shot install
└── run.sh              Starts backend + frontend
```

## Music engines

MusiGen supports three music engines, picked automatically in this order
(you can also force one from the System panel):

| Engine     | What it is                                              | Setup effort | Real music? |
|------------|---------------------------------------------------------|--------------|-------------|
| `comfy`    | MiniMax-Music3-GGUF running inside a local ComfyUI      | High         | Yes         |
| `musicgen` | Meta MusicGen via `transformers` (CPU / MPS / CUDA)     | Low          | Yes         |
| `stub`     | Synthesised placeholder chord, fallback for UI testing  | None         | **No**      |

If you see a red "STUB MODE" banner in the UI, the app fell through to the
placeholder — install one of the real engines below.

## Quick start (fastest path to real music)

```bash
# 1. Install base deps (Python + Node)
./setup.sh

# 2. Prompt copilot LLM
./scripts/download_llm.sh

# 3. Real music engine (MusicGen, ~1.2 GB, works on Mac / CPU / GPU)
./scripts/download_musicgen.sh

# 4. Run the app
./run.sh
```

Open http://localhost:5173 and you're in.

## Full path (MiniMax-Music3 via ComfyUI)

Higher quality, more setup:

```bash
./scripts/download_music_model.sh          # MiniMax GGUF + companion files
./scripts/install_comfyui.sh               # clone ComfyUI + ComfyUI-GGUF
cd ComfyUI && source .venv/bin/activate && python main.py --port 8188
```

The backend auto-switches to `comfy` once ComfyUI is reachable and all
three files (music GGUF + text encoder + VAE) are present under
`Models/music/`.

## Config

The backend reads its config from environment variables (all optional):

| Variable                 | Default                                | Meaning |
|--------------------------|----------------------------------------|---------|
| `MUSIGEN_ROOT`           | project root                           | Base dir for models/outputs |
| `MUSIGEN_MODELS_DIR`     | `Models/`                              | Where to look for GGUF files |
| `MUSIGEN_OUTPUTS_DIR`    | `Outputs/`                             | Where to save generated audio |
| `MUSIGEN_LLM_MODEL`      | auto-detected `Models/llm/*.gguf`      | Path to the LLM GGUF |
| `MUSIGEN_LLM_CTX`        | `4096`                                 | Context length for the LLM |
| `MUSIGEN_LLM_GPU_LAYERS` | `0`                                    | Layers to offload to GPU |
| `MUSIGEN_COMFY_URL`      | `http://127.0.0.1:8188`                | ComfyUI HTTP endpoint |
| `MUSIGEN_MUSIC_ENGINE`   | `auto`                                 | `auto`, `comfy`, or `stub` |
| `MUSIGEN_HOST`           | `127.0.0.1`                            | Bind host |
| `MUSIGEN_PORT`           | `8000`                                 | Bind port |

## Prompting these models

The MiniMax Music model wants two things:

1. **Lyrics** — verse/chorus/bridge, or empty for an instrumental
2. **Description** — a paragraph naming genre, instruments, tempo (BPM),
   mood, era, production style, mixing cues, energy level

The prompt copilot in the UI (the sparkle button on any input) will
convert a one-line idea like *"chill boom-bap for late night coding"*
into something the model can actually use.

## License

MIT — do what you like.
