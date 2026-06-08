# 🎙️ Offline Speech Assistant

A fully offline, privacy-first voice assistant powered by **Whisper**, **Ollama**, and **Piper TTS**. Supports **English** and **German** with automatic language detection.

```
🎤 Microphone → Silero VAD → faster-whisper (STT + Lang) → Ollama LLM → Piper TTS → 🔊 Speaker
```

## Features

- **100% Offline** — No data leaves your machine after initial model downloads
- **Bilingual** — Speaks and understands English and German
- **Automatic Language Detection** — Detects language from your speech and responds accordingly
- **Conversation Memory** — Remembers context within a session
- **Voice Activity Detection** — Smart silence detection, no push-to-talk needed
- **GPU Accelerated** — Runs on CUDA for fast transcription

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| STT | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (medium) | Speech-to-Text + Language Detection |
| LLM | [Ollama](https://ollama.com/) (qwen3.5:9b) | Local AI chat |
| TTS | [Piper](https://github.com/rhasspy/piper) | Neural Text-to-Speech |
| VAD | [Silero VAD](https://github.com/snakers4/silero-vad) | Voice Activity Detection |

## Requirements

- **Python** 3.10+
- **CUDA GPU** with 16GB+ VRAM (recommended)
- **Ollama** installed and running
- **FFmpeg** installed
- **Microphone** connected

## Installation

### 1. Clone and setup
```bash
git clone https://github.com/asw-02/offline-voice-assistant.git
cd offline-voice-assistant

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### 2. Install Ollama
Download from [ollama.com](https://ollama.com/), then:
```bash
ollama pull qwen3.5:9b
```

### 3. Install FFmpeg
```bash
# Windows (via Chocolatey)
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

### 4. Download Models
```bash
python scripts/download_models.py
```

This downloads:
- Piper TTS binary (Windows)
- English voice model (`en_US-lessac-medium`)
- German voice model (`de_DE-thorsten-medium`)
- Pre-caches Whisper and Silero VAD models

## Usage

### Start Ollama (if not already running)
```bash
ollama serve
```

### Run the Assistant
```bash
python main.py
```

## Raspberry Pi 5 (aarch64) Quickstart

On a Raspberry Pi 5 (8GB) use the provided setup script to install system deps, create a venv, and download models:

```bash
bash scripts/setup_pi.sh
source venv/bin/activate
ollama serve   # if Ollama is installed
python main.py
```

Notes:
- This build uses Vosk for STT, an RMS-based VAD, Ollama via HTTP, and Piper piped to `aplay` for TTS.
- Recommended Ollama model: `qwen3.5:2b` for 8GB RAM. `qwen3.5:9b` is too large for the Pi.

### Voice Commands
- Say **"reset"** or **"zurücksetzen"** — Clear conversation history
- Say **"exit"**, **"quit"**, or **"beenden"** — Stop the assistant
- Press **Ctrl+C** — Graceful shutdown

## Configuration

Edit `config.py` to tune:

| Setting | Default | Description |
|---|---|---|
| `WHISPER_MODEL_SIZE` | `medium` | Whisper model (`tiny`/`base`/`small`/`medium`/`large-v3`) |
| `WHISPER_DEVICE` | `cuda` | `cuda` for GPU, `cpu` for CPU |
| `OLLAMA_MODEL` | `qwen3.5:9b` | Any Ollama model |
| `VAD_THRESHOLD` | `0.5` | Speech detection sensitivity (0-1) |
| `SILENCE_DURATION` | `1.5` | Seconds of silence before processing |
| `MAX_CONVERSATION_HISTORY` | `10` | Message pairs to remember |

## Project Structure

```
offline_speech_assistent/
├── main.py                     # Entry point
├── config.py                   # All configuration
├── requirements.txt            # Python dependencies
├── assistant/
│   ├── audio_capture.py        # Microphone + Silero VAD
│   ├── language_detector.py    # EN/DE language detection
│   ├── transcriber.py          # faster-whisper STT
│   ├── llm_client.py           # Ollama integration
│   ├── tts_engine.py           # Piper TTS wrapper
│   └── audio_player.py         # WAV playback
├── models/piper/               # Voice model files
├── tools/piper/                # Piper binary
└── scripts/
    └── download_models.py      # Model downloader
```

## License

MIT
