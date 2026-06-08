"""
RMS-based microphone capture for Raspberry Pi.

Provides `listen_for_speech()` which records to a WAV file
using a simple RMS-start / RMS-silence detector adapted from the
reference project.
"""

import time
import wave
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd

import config


def _rms_from_int16(block: np.ndarray) -> float:
    """Calculate RMS from int16 audio block."""
    if block is None or len(block) == 0:
        return 0.0
    arr = block.astype(np.float32)
    return float(np.sqrt(np.mean((arr / 32768.0) ** 2)))


class AudioCapture:
    """Capture audio from the default (or configured) microphone.

    listen_for_speech() records into `config.OUTPUT_WAV` and returns
    the Path to the written WAV file, or None on timeout/short audio.
    """

    def __init__(self):
        self.sample_rate = config.SAMPLE_RATE
        self.channels = config.CHANNELS
        self.blocksize = config.BLOCKSIZE
        self.mic_device = config.MIC_DEVICE

    def listen_for_speech(self) -> Optional[Path]:
        """Listen until speech is detected and ends; write WAV and return Path."""
        start_threshold = config.START_RMS
        stop_threshold = config.STOP_RMS
        silence_seconds = config.SILENCE_SECONDS
        min_seconds = config.MIN_RECORD_SECONDS
        timeout = config.LISTEN_TIMEOUT_SECONDS

        frames: list[bytes] = []

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.blocksize,
                dtype="int16",
                channels=self.channels,
                device=self.mic_device,
            ) as stream:

                print("[LISTEN] Waiting for speech...")
                # Estimate noise floor from a brief initial sample
                noise_samples = []
                noise_start = time.time()
                while time.time() - noise_start < 0.5:
                    data, _ = stream.read(self.blocksize)
                    noise_samples.append(np.frombuffer(data, dtype=np.int16))
                noise_rms = np.mean([_rms_from_int16(s) for s in noise_samples])
                start_rms = max(start_threshold / 32768.0, noise_rms * 3.0)
                stop_rms = max(stop_threshold / 32768.0, noise_rms * 1.8)

                # Wait for speech start
                started = False
                speech_start_time = None
                silence_start_time = None
                overall_start = time.time()

                while True:
                    if time.time() - overall_start > timeout:
                        print("[LISTEN] Timeout waiting for speech")
                        return None

                    data, _ = stream.read(self.blocksize)
                    block = np.frombuffer(data, dtype=np.int16)
                    rms = _rms_from_int16(block)

                    if not started:
                        if rms >= start_rms:
                            started = True
                            speech_start_time = time.time()
                            frames.append(data)
                            silence_start_time = None
                            print("[LISTEN] Speech started")
                        else:
                            # keep waiting
                            continue
                    else:
                        frames.append(data)
                        if rms < stop_rms:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            elif time.time() - silence_start_time >= silence_seconds:
                                # finished
                                break
                        else:
                            silence_start_time = None

                # Validate minimum duration
                if speech_start_time is None:
                    return None
                duration = time.time() - speech_start_time
                if duration < min_seconds:
                    print("[LISTEN] Speech too short")
                    return None

                # Write WAV file (16-bit PCM)
                out_path = Path(config.OUTPUT_WAV)
                with wave.open(str(out_path), "wb") as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b"".join(frames))

                print(f"[LISTEN] Recorded {duration:.2f}s -> {out_path}")
                return out_path

        except Exception as e:
            print(f"  [!!] Audio capture error: {e}")
            return None

    def cleanup(self) -> None:
        pass
