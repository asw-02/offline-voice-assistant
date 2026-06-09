#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Microphone audio capture with RMS-based Voice Activity Detection.

Adapted from the reference alarm project:
  voice_control/qwen_assistant.py -> record_until_silence()

Uses sounddevice InputStream with an adaptive noise floor.
No ML model required — purely amplitude-based detection.
"""

import queue
import time
import wave

import numpy as np
import sounddevice as sd

import config


class AudioCapture:
    """Captures speech from the microphone using RMS-based VAD."""

    def __init__(
        self,
        mic_device=config.MIC_DEVICE,
        sample_rate=config.SAMPLE_RATE,
        channels=config.CHANNELS,
        blocksize=config.BLOCKSIZE,
    ):
        self._mic_device = mic_device
        self._sample_rate = sample_rate
        self._channels = channels
        self._blocksize = blocksize

        # Verify microphone is accessible
        try:
            sd.check_input_settings(
                device=self._mic_device,
                channels=self._channels,
                samplerate=self._sample_rate,
            )
            print("[MIC] Microphone OK")
        except Exception as exc:
            print(f"[!!] Microphone check failed: {exc}")
            raise

    @staticmethod
    def calculate_rms(audio_block):
        """Calculate Root Mean Square of an audio block."""
        audio_float = audio_block.astype(np.float32)
        return float(np.sqrt(np.mean(audio_float ** 2)))

    def record_until_silence(self, filename=config.OUTPUT_WAV):
        """
        Record from microphone until speech is detected and then silence follows.

        Adapted from reference project's record_until_silence().

        Returns:
            True if speech was captured and saved to WAV, False otherwise.
        """
        print("\n[MIC] Listening...")

        recorded_blocks = []
        speech_started = False
        input_queue = queue.Queue(maxsize=80)
        input_overflows = 0
        dropped_blocks = 0

        start_time = time.monotonic()
        speech_start_time = None
        last_voice_time = start_time
        noise_rms = min(config.START_RMS, config.STOP_RMS) / 2.0

        def audio_callback(indata, frames, time_info, status):
            nonlocal dropped_blocks, input_overflows

            if status:
                input_overflows += 1

            try:
                input_queue.put_nowait(indata.copy())
            except queue.Full:
                dropped_blocks += 1
                try:
                    input_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    input_queue.put_nowait(indata.copy())
                except queue.Full:
                    pass

        try:
            with sd.InputStream(
                device=self._mic_device,
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="int16",
                blocksize=self._blocksize,
                latency="high",
                callback=audio_callback,
            ):
                while True:
                    try:
                        audio_block = input_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue

                    if input_overflows:
                        print(f"[MIC] Audio overflow ({input_overflows}x)")
                        input_overflows = 0

                    if dropped_blocks:
                        print(f"[MIC] Buffer full, {dropped_blocks} block(s) dropped")
                        dropped_blocks = 0

                    rms = self.calculate_rms(audio_block.reshape(-1))
                    now = time.monotonic()
                    recorded_blocks.append(audio_block.copy())

                    start_threshold = max(config.START_RMS, noise_rms * 3.0)
                    stop_threshold = max(config.STOP_RMS, noise_rms * 1.8)

                    if not speech_started:
                        if rms >= start_threshold:
                            speech_started = True
                            speech_start_time = now
                            last_voice_time = now
                            print("[MIC] Speech detected, recording...")
                        else:
                            # Adapt noise floor
                            noise_rms = (noise_rms * 0.95) + (rms * 0.05)
                            if now - start_time >= config.LISTEN_TIMEOUT_SECONDS:
                                print("[MIC] No speech detected (timeout)")
                                return False
                            continue
                    else:
                        if rms >= stop_threshold:
                            last_voice_time = now

                        silence_duration = now - last_voice_time
                        record_duration = now - speech_start_time

                        if (
                            silence_duration >= config.SILENCE_SECONDS
                            and record_duration >= config.MIN_RECORD_SECONDS
                        ):
                            print("[MIC] Silence detected, recording stopped")
                            break

        except Exception as exc:
            print(f"[!!] Recording error: {exc}")
            return False

        if not speech_started or not recorded_blocks:
            print("[MIC] No speech detected")
            return False

        # Concatenate and save as WAV
        audio = np.concatenate(recorded_blocks, axis=0)

        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self._channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self._sample_rate)
                wf.writeframes(audio.tobytes())
            return True
        except Exception as exc:
            print(f"[!!] Error saving WAV: {exc}")
            return False

    def listen_for_speech(self):
        """Listen for speech and return the Path to the recorded WAV, or None.

        This is the high-level API used by main.py.
        """
        from pathlib import Path

        success = self.record_until_silence(config.OUTPUT_WAV)
        if success:
            return Path(config.OUTPUT_WAV)
        return None

    def cleanup(self):
        """Release audio resources."""
        print("[MIC] Audio resources released")
