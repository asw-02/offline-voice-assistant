#!/usr/bin/env bash

set -euo pipefail

echo "[SETUP] Installing system packages..."
sudo apt-get update
sudo apt-get install -y portaudio19-dev alsa-utils libsndfile1

echo "[SETUP] Creating virtualenv and installing Python deps..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[SETUP] Downloading Vosk models (English + German)..."
mkdir -p models
cd models
if [ ! -d "vosk-model-de-0.21" ]; then
  wget -c https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip
  unzip -o vosk-model-de-0.21.zip && rm -f vosk-model-de-0.21.zip
fi
if [ ! -d "vosk-model-en-us-0.22" ]; then
  wget -c https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
  unzip -o vosk-model-en-us-0.22.zip && rm -f vosk-model-en-us-0.22.zip
fi
cd -

echo "[SETUP] (Optional) Install Piper binary and voices under tools/piper"
# Add instructions for Piper download; user must choose appropriate binary for aarch64

echo "[SETUP] Pull Ollama model (if Ollama is installed on Pi)"
# ollama pull qwen3:1.7b

echo "[SETUP] Done. Activate the venv with: source venv/bin/activate"
