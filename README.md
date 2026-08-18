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

## Quick start

```bash
# 1. Install everything (Python + Node deps)
./setup.sh

# 2. Download models (choose sizes interactively)
./scripts/download_music_model.sh
./scripts/download_llm.sh

# 3. (Optional) Install ComfyUI locally, or point MUSIGEN_COMFY_URL
#    at an existing ComfyUI instance
./scripts/install_comfyui.sh

# 4. Run the app
./run.sh
```

Open http://localhost:5173 and you're in.

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
