#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Central configuration for the Offline Speech Assistant (Raspberry Pi 5).
All tuneable parameters live here.
"""

from pathlib import Path

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
TEMP_DIR = PROJECT_ROOT / "temp"

# ──────────────────────────────────────────────
# Audio Capture & Recording
# ──────────────────────────────────────────────
MIC_DEVICE = None             # None = system default, or integer device index
SAMPLE_RATE = 16000           # Hz — Vosk standard
CHANNELS = 1                  # Mono
BLOCKSIZE = 4096              # Samples per recording block

# RMS-based Voice Activity Detection
START_RMS = 300               # RMS threshold to start recording
STOP_RMS = 200                # RMS threshold to detect silence
SILENCE_SECONDS = 1.5         # Seconds of silence before ending recording
MIN_RECORD_SECONDS = 0.5      # Minimum speech duration to process
LISTEN_TIMEOUT_SECONDS = 8    # Max wait for speech before giving up
OUTPUT_WAV = str(TEMP_DIR / "recording.wav")

# ──────────────────────────────────────────────
# Speech-to-Text (Vosk)
# ──────────────────────────────────────────────
VOSK_MODEL_PATHS = {
    "de": str(MODELS_DIR / "vosk-model-de-0.21"),
    "en": str(MODELS_DIR / "vosk-model-en-us-0.22"),
}
SUPPORTED_LANGUAGES = ["en", "de"]
DEFAULT_LANGUAGE = "de"

# ──────────────────────────────────────────────
# LLM (Ollama via requests)
# ──────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3.5:2b"
OLLAMA_TIMEOUT = 30           # seconds max for LLM response
MAX_CONVERSATION_HISTORY = 5  # Max messages to keep (pairs, not including system)

OLLAMA_OPTIONS = {
    "num_ctx": 768,
    "num_thread": 3,
    "num_predict": 120,
    "temperature": 0.2,
}

SYSTEM_PROMPTS = {
    "en": (
        "You are a helpful voice assistant. "
        "Always address the user informally. "
        "Keep your answers short, direct, and natural in at most four to five sentences. "
        "No lists, no markdown, no emojis. "
        "You have no internet access. Do not claim any current weather, "
        "news, stock, traffic, opening hours, or live data. "
        "If a question requires current online data, say clearly that you "
        "have no internet access. "
        "If a request is unclear, answer exactly: "
        "'I don't understand. Can you please repeat that?'"
    ),
    "de": (
        "Du bist ein deutscher Sprachassistent. "
        "Sprich den Nutzer immer mit du an, nie mit Sie. "
        "Antworte kurz, direkt und natuerlich in maximal vier bis fuenf Saetzen. "
        "Keine Listen, kein Markdown, keine Emojis. "
        "Du hast keinen Internetzugriff. Behaupte keine aktuellen Wetter-, "
        "Nachrichten-, Kurs-, Verkehrs-, Oeffnungszeiten- oder Live-Daten. "
        "Wenn eine Frage aktuelle Online-Daten benoetigt, sage klar, dass du "
        "keinen Internetzugriff hast. "
        "Wenn eine Anfrage unklar ist, antworte genau: "
        "'Ich verstehe nicht. Kannst du es bitte wiederholen?'"
    ),
}

# ──────────────────────────────────────────────
# Text-to-Speech (Piper)
# ──────────────────────────────────────────────
PIPER_BIN = str(PROJECT_ROOT / "tools" / "piper" / "piper")

PIPER_VOICE_MODELS = {
    "en": str(MODELS_DIR / "piper" / "en_US-lessac-medium.onnx"),
    "de": str(MODELS_DIR / "piper" / "de_DE-thorsten-medium.onnx"),
}

# Piper output sample rate (must match voice model)
PIPER_SAMPLE_RATE = 22050

# ──────────────────────────────────────────────
# Language Detection
# ──────────────────────────────────────────────
# Seconds of audio to use for language detection (from start of recording)
LANG_DETECT_SECONDS = 3.0

# ──────────────────────────────────────────────
# False positive filtering (from reference project)
# ──────────────────────────────────────────────
FALSE_POSITIVE_PHRASES = {
    "nun", "nun einen", "nun eine", "einen", "eine",
    "und", "äh", "ähm", "hm", "hmm",
    "the", "a", "an", "um", "uh",
}

FILLER_WORDS = {
    "nun", "einen", "eine", "ein", "und", "äh", "ähm", "hm", "hmm",
    "the", "a", "an", "um", "uh", "oh",
}

# ──────────────────────────────────────────────
# Ensure directories exist
# ──────────────────────────────────────────────
TEMP_DIR.mkdir(parents=True, exist_ok=True)
(MODELS_DIR / "piper").mkdir(parents=True, exist_ok=True)
