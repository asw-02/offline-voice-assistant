#!/bin/bash
# =============================================================================
# Offline Speech Assistant -- Raspberry Pi 5 Setup Script
#
# Installs system dependencies, Python packages, Vosk models, Piper binary,
# and Piper voice models. Run this once after cloning the repository.
#
# Usage:
#   chmod +x scripts/setup_pi.sh
#   bash scripts/setup_pi.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_DIR/models"
PIPER_MODELS_DIR="$MODELS_DIR/piper"
TOOLS_DIR="$PROJECT_DIR/tools/piper"

echo "=================================================="
echo "  Offline Speech Assistant -- Pi 5 Setup"
echo "=================================================="

# --- System dependencies ---------------------------------------------------
echo ""
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    portaudio19-dev \
    alsa-utils \
    unzip \
    wget

# --- Python virtual environment --------------------------------------------
echo ""
echo "[2/6] Setting up Python virtual environment..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
    echo "  [OK] venv created"
else
    echo "  [OK] venv already exists"
fi

source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$PROJECT_DIR/requirements.txt" -q
echo "  [OK] Python packages installed"

# --- Vosk models -----------------------------------------------------------
echo ""
echo "[3/6] Downloading Vosk speech models..."

mkdir -p "$MODELS_DIR"

# German model
if [ -d "$MODELS_DIR/vosk-model-de-0.21" ]; then
    echo "  [OK] German Vosk model already exists"
else
    echo "  [>>] Downloading German Vosk model (~1.6 GB)..."
    wget -q --show-progress -O "$MODELS_DIR/vosk-model-de-0.21.zip" \
        "https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip"
    echo "  [..] Extracting..."
    unzip -q "$MODELS_DIR/vosk-model-de-0.21.zip" -d "$MODELS_DIR"
    rm "$MODELS_DIR/vosk-model-de-0.21.zip"
    echo "  [OK] German Vosk model ready"
fi

# English model
if [ -d "$MODELS_DIR/vosk-model-en-us-0.22" ]; then
    echo "  [OK] English Vosk model already exists"
else
    echo "  [>>] Downloading English Vosk model (~1.8 GB)..."
    wget -q --show-progress -O "$MODELS_DIR/vosk-model-en-us-0.22.zip" \
        "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
    echo "  [..] Extracting..."
    unzip -q "$MODELS_DIR/vosk-model-en-us-0.22.zip" -d "$MODELS_DIR"
    rm "$MODELS_DIR/vosk-model-en-us-0.22.zip"
    echo "  [OK] English Vosk model ready"
fi

# --- Piper TTS binary ------------------------------------------------------
echo ""
echo "[4/6] Downloading Piper TTS binary..."

mkdir -p "$TOOLS_DIR"

if [ -f "$TOOLS_DIR/piper" ]; then
    echo "  [OK] Piper binary already exists"
else
    echo "  [>>] Downloading Piper for Linux aarch64..."
    wget -q --show-progress -O "$TOOLS_DIR/piper_linux_aarch64.tar.gz" \
        "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz"
    echo "  [..] Extracting..."
    tar -xzf "$TOOLS_DIR/piper_linux_aarch64.tar.gz" -C "$TOOLS_DIR" --strip-components=1
    rm "$TOOLS_DIR/piper_linux_aarch64.tar.gz"
    chmod +x "$TOOLS_DIR/piper"
    echo "  [OK] Piper binary ready"
fi

# --- Piper voice models ----------------------------------------------------
echo ""
echo "[5/6] Downloading Piper voice models..."

mkdir -p "$PIPER_MODELS_DIR"

# English voice
if [ -f "$PIPER_MODELS_DIR/en_US-lessac-medium.onnx" ]; then
    echo "  [OK] English voice already exists"
else
    echo "  [>>] Downloading English voice..."
    wget -q --show-progress -O "$PIPER_MODELS_DIR/en_US-lessac-medium.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    wget -q -O "$PIPER_MODELS_DIR/en_US-lessac-medium.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    echo "  [OK] English voice ready"
fi

# German voice
if [ -f "$PIPER_MODELS_DIR/de_DE-thorsten-medium.onnx" ]; then
    echo "  [OK] German voice already exists"
else
    echo "  [>>] Downloading German voice..."
    wget -q --show-progress -O "$PIPER_MODELS_DIR/de_DE-thorsten-medium.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx"
    wget -q -O "$PIPER_MODELS_DIR/de_DE-thorsten-medium.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json"
    echo "  [OK] German voice ready"
fi

# --- Ollama model -----------------------------------------------------------
echo ""
echo "[6/6] Checking Ollama..."

if command -v ollama &> /dev/null; then
    echo "  [OK] Ollama is installed"
    echo "  [>>] Pulling qwen3:1.7b model..."
    ollama pull qwen3:1.7b || echo "  [!!] Failed to pull model. Run manually: ollama pull qwen3:1.7b"
else
    echo "  [!!] Ollama is not installed"
    echo "  Install from: https://ollama.com/"
    echo "  Then run: ollama pull qwen3:1.7b"
fi

# --- Done -------------------------------------------------------------------
echo ""
echo "=================================================="
echo "  Setup complete!"
echo "=================================================="
echo ""
echo "To run the assistant:"
echo "  source venv/bin/activate"
echo "  ollama serve  (in another terminal, if not running)"
echo "  python3 main.py"
