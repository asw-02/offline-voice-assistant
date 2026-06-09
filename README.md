# 🎙️ Offline Speech Assistant — Raspberry Pi 5

A fully offline, privacy-first voice assistant for **Raspberry Pi 5** powered by **Vosk**, **Ollama**, and **Piper TTS**. Supports **English** and **German** with automatic language detection.

```
🎤 Microphone → RMS VAD → Vosk STT (EN + DE) → Ollama LLM → Piper TTS → 🔊 Speaker
```

## Features

- **100% Offline** — No data leaves your device after initial model downloads
- **Bilingual** — Speaks and understands English and German
- **Automatic Language Detection** — Dual-Vosk confidence comparison picks the right language
- **Conversation Memory** — Remembers context within a session (last 5 message pairs)
- **RMS-based VAD** — Adaptive noise-floor detection, no push-to-talk needed
- **Lightweight** — No PyTorch, no GPU — runs entirely on CPU

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| STT | [Vosk](https://alphacephei.com/vosk/) (DE 0.21 + EN 0.22) | Speech-to-Text |
| Language Detection | Dual-Vosk models | Confidence comparison across EN and DE |
| LLM | [Ollama](https://ollama.com/) (`qwen3.5:2b`) | Local AI chat via HTTP |
| TTS | [Piper](https://github.com/rhasspy/piper) → `aplay` | Neural Text-to-Speech |
| VAD | RMS-based (adaptive noise floor) | Voice Activity Detection |

## Requirements

- **Raspberry Pi 5** (8 GB RAM recommended)
- **Python** 3.10+
- **Ollama** installed and running
- **Microphone** connected (USB or I²S)
- **Speaker** via 3.5mm jack or HDMI

## Quick Setup

```bash
git clone https://github.com/asw-02/offline-voice-assistant.git
cd offline-voice-assistant

chmod +x scripts/setup_pi.sh
bash scripts/setup_pi.sh
```

The setup script handles everything:
1. Installs system packages (`portaudio19-dev`, `alsa-utils`)
2. Creates a Python virtual environment
3. Downloads Vosk models (~3.4 GB total)
4. Downloads Piper binary (aarch64) and voice models (EN + DE)
5. Pulls the Ollama model (`qwen3:1.7b`)

## Usage

### Start Ollama (if not already running)
```bash
ollama serve
```

### Run the Assistant
```bash
source venv/bin/activate
python3 main.py
```

### Voice Commands
- Say **"reset"** or **"zurücksetzen"** — Clear conversation history
- Say **"exit"**, **"quit"**, or **"beenden"** — Stop the assistant
- Press **Ctrl+C** — Graceful shutdown

## Configuration

Edit `config.py` to tune:

| Setting | Default | Description |
|---|---|---|
| `MIC_DEVICE` | `None` (system default) | Microphone device index |
| `START_RMS` / `STOP_RMS` | `300` / `200` | RMS thresholds for speech detection |
| `SILENCE_SECONDS` | `1.5` | Seconds of silence before processing |
| `OLLAMA_MODEL` | `qwen3.5:2b` | Any Ollama model |
| `MAX_CONVERSATION_HISTORY` | `5` | Message pairs to remember |
| `LANG_DETECT_SECONDS` | `3.0` | Audio prefix used for language detection |

## Project Structure

```
offline_speech_assistent/
├── main.py                     # Entry point — orchestrates the pipeline
├── config.py                   # All configuration (paths, thresholds, models)
├── requirements.txt            # Python deps: vosk, sounddevice, numpy, requests
├── assistant/
│   ├── __init__.py
│   ├── audio_capture.py        # RMS-based VAD microphone capture
│   ├── language_detector.py    # Dual-Vosk language detection
│   ├── transcriber.py          # Vosk WAV transcription
│   ├── llm_client.py           # Ollama HTTP client
│   ├── tts_engine.py           # Piper → aplay pipe
│   └── speech_format.py        # German text formatting for TTS
├── models/
│   ├── vosk-model-de-0.21/     # German Vosk model (~1.6 GB)
│   ├── vosk-model-en-us-0.22/  # English Vosk model (~1.8 GB)
│   └── piper/                  # Piper voice .onnx files
├── tools/piper/                # Piper binary (aarch64)
└── scripts/
    └── setup_pi.sh             # One-shot Pi setup script
```

## RAM Budget (Pi 5, 8 GB)

| Component | Approximate Usage |
|---|---|
| Vosk DE model | ~1.6 GB |
| Vosk EN model | ~1.8 GB |
| Ollama (qwen3.5:2b) | ~1.5 GB |
| Python + Piper | ~0.3 GB |
| **Total** | **~5.2 GB** |

## License

MIT
