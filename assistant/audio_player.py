"""
Audio playback for WAV files.

Uses sounddevice for cross-platform audio output.
"""

from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    """Plays WAV audio files through the default output device."""

    def play(self, wav_path: str | Path) -> None:
        """
        Play a WAV file synchronously (blocks until playback finishes).

        Args:
            wav_path: Path to the WAV file to play.
        """
        wav_path = Path(wav_path)
        if not wav_path.exists():
            print(f"  [!!] Audio file not found: {wav_path}")
            return

        try:
            # Read the WAV file
            data, sample_rate = sf.read(wav_path, dtype="float32")

            # Play and wait for completion
            sd.play(data, samplerate=sample_rate)
            sd.wait()

        except Exception as e:
            print(f"  [!!] Playback error: {e}")

    def play_array(self, audio: np.ndarray, sample_rate: int = 22050) -> None:
        """
        Play a numpy audio array synchronously.

        Args:
            audio: Audio data as float32 numpy array.
            sample_rate: Sample rate of the audio.
        """
        try:
            sd.play(audio, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            print(f"  [!!] Playback error: {e}")
