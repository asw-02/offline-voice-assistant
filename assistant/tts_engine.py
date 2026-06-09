#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text-to-Speech engine using Piper TTS piped to aplay.

Adapted from the reference alarm project:
  voice_control/qwen_assistant.py -> speak()

Pipes text to Piper's stdin, Piper's raw audio stdout to aplay
for real-time streaming playback on Linux/Raspberry Pi.
"""

import subprocess
import time
from pathlib import Path

import config
from assistant.speech_format import format_for_tts


class TTSEngine:
    """Wraps Piper TTS for offline text-to-speech on Linux."""

    def __init__(
        self,
        piper_binary=config.PIPER_BIN,
        voice_models=None,
    ):
        self._binary = piper_binary
        self._voice_models = voice_models or config.PIPER_VOICE_MODELS

        # Validate binary exists
        if not Path(self._binary).exists():
            raise FileNotFoundError(
                f"Piper binary not found at {self._binary}\n"
                "Run: bash scripts/setup_pi.sh"
            )

        # Validate voice models exist
        for lang, model_path in self._voice_models.items():
            if not Path(model_path).exists():
                raise FileNotFoundError(
                    f"Piper voice model for '{lang}' not found at {model_path}\n"
                    "Run: bash scripts/setup_pi.sh"
                )

        print("[TTS] Piper TTS ready")
        for lang, model_path in self._voice_models.items():
            print(f"   {lang}: {Path(model_path).name}")

    def speak(self, text, language, should_stop=None):
        """
        Synthesize and play text using Piper piped to aplay.

        Adapted from reference project's speak() method.
        Pipes: text -> piper stdin -> piper stdout (raw audio) -> aplay

        Args:
            text: The text to speak.
            language: Language code ("en" or "de") to select voice.
            should_stop: Optional callable that returns True to abort playback.
        """
        if not text:
            return

        # Select voice model
        model_path = self._voice_models.get(language)
        if model_path is None:
            print(f"[TTS] No voice for '{language}', falling back to English")
            model_path = self._voice_models.get("en", "")

        # Apply German time formatting
        if language == "de":
            spoken_text = format_for_tts(text)
        else:
            spoken_text = text

        piper = None
        aplay = None

        try:
            # Start Piper (with nice for lower CPU priority on Pi)
            piper = subprocess.Popen(
                [
                    "nice", "-n", "15",
                    self._binary,
                    "--model", model_path,
                    "--output-raw",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )

            # Pipe Piper's raw output to aplay
            aplay = subprocess.Popen(
                [
                    "aplay",
                    "-r", str(config.PIPER_SAMPLE_RATE),
                    "-f", "S16_LE",
                    "-t", "raw",
                    "-",
                ],
                stdin=piper.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Send text and close stdin
            piper.stdin.write(spoken_text)
            piper.stdin.close()

            # Wait for playback to finish (with interruptibility)
            while True:
                piper_done = piper.poll() is not None
                aplay_done = aplay.poll() is not None

                if piper_done and aplay_done:
                    break

                if should_stop is not None and should_stop():
                    print("[TTS] Playback interrupted")
                    for process in [piper, aplay]:
                        if process and process.poll() is None:
                            process.kill()
                    return

                time.sleep(0.05)

        except Exception as exc:
            print(f"[!!] TTS error: {exc}")

            for process in [piper, aplay]:
                if process:
                    try:
                        process.kill()
                    except Exception:
                        pass
