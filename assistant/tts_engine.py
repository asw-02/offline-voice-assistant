"""
Piper TTS engine that pipes synthesized PCM into `aplay` for playback.

This is designed for Linux (Raspberry Pi) where `aplay` is available.
"""

import shlex
import subprocess
from pathlib import Path
from typing import Callable

import config


class TTSEngine:
    def __init__(self):
        self.piper = Path(config.PIPER_BIN)
        self.voice_models = config.PIPER_VOICE_MODELS

        if not self.piper.exists():
            raise FileNotFoundError(f"Piper binary not found at {self.piper}")

        for lang, model in self.voice_models.items():
            if not Path(model).exists():
                print(f"  [WARN] Piper model for {lang} missing: {model}")

        print("[TTS] Piper TTS ready (will pipe to aplay)")

    def speak(self, text: str, language: str, should_stop: Callable[[], bool] | None = None) -> None:
        """Synthesize `text` and play immediately via `aplay`.

        `should_stop` can be passed to interrupt long playback (not implemented
        in this simple version but kept for API compatibility).
        """
        model = self.voice_models.get(language) or self.voice_models.get("en")
        if model is None:
            raise RuntimeError("No Piper voice model configured")

        # Ensure text is shell-safe
        quoted = shlex.quote(text)

        cmd = (
            f"echo {quoted} | nice -n 15 {shlex.quote(str(self.piper))} --model {shlex.quote(str(model))} --output-raw - "
            f"| aplay -r {config.PIPER_SAMPLE_RATE} -f S16_LE -t raw -"
        )

        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"  [!!] TTS playback failed: {e}")

    def cleanup_temp_files(self) -> None:
        return
