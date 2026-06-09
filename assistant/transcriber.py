#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Speech-to-Text transcription using Vosk.

Adapted from the reference alarm project:
  voice_control/qwen_assistant.py -> transcribe_wav(), normalize_text()

Reads a WAV file and returns the recognized text.
"""

import json
import wave
from pathlib import Path

from vosk import KaldiRecognizer, Model

import config


class Transcriber:
    """Wraps Vosk for offline speech-to-text transcription."""

    def __init__(self):
        self._models = {}

    def load_model(self, language):
        """Load a Vosk model for the given language, with caching."""
        if language in self._models:
            return self._models[language]

        model_path = config.VOSK_MODEL_PATHS.get(language)
        if not model_path:
            raise ValueError(f"No Vosk model configured for language '{language}'")

        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Vosk model not found at {model_path}\n"
                f"Download it from https://alphacephei.com/vosk/models"
            )

        print(f"[STT] Loading Vosk model for '{language}'...")
        model = Model(model_path)
        self._models[language] = model
        print(f"  [OK] Vosk model '{language}' loaded")
        return model

    def transcribe_wav(self, filename, language):
        """
        Transcribe a WAV file using Vosk.

        Adapted from reference project's transcribe_wav().

        Args:
            filename: Path to the WAV file.
            language: Language code ("en" or "de") to select the model.

        Returns:
            Recognized text as a string (normalized).
        """
        wav_path = Path(filename)
        if not wav_path.exists():
            print(f"[!!] WAV file not found: {filename}")
            return ""

        model = self.load_model(language)

        try:
            wf = wave.open(str(wav_path), "rb")
        except Exception as exc:
            print(f"[!!] Error opening WAV: {exc}")
            return ""

        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognizer.SetWords(False)

        text_parts = []

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    text_parts.append(text)

        final_result = json.loads(recognizer.FinalResult())
        final_text = final_result.get("text", "").strip()
        if final_text:
            text_parts.append(final_text)

        wf.close()
        return self.normalize_text(" ".join(text_parts).strip())

    def transcribe_wav_with_confidence(self, filename, language):
        """
        Transcribe a WAV file and return text + word-level confidence.

        Used by the LanguageDetector to compare recognition quality.

        Returns:
            Tuple of (text, average_confidence).
        """
        wav_path = Path(filename)
        if not wav_path.exists():
            return "", 0.0

        model = self.load_model(language)

        try:
            wf = wave.open(str(wav_path), "rb")
        except Exception:
            return "", 0.0

        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognizer.SetWords(True)  # Enable word-level confidence

        all_words = []
        all_confidences = []

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                for word_info in result.get("result", []):
                    all_words.append(word_info.get("word", ""))
                    all_confidences.append(word_info.get("conf", 0.0))

        final_result = json.loads(recognizer.FinalResult())
        for word_info in final_result.get("result", []):
            all_words.append(word_info.get("word", ""))
            all_confidences.append(word_info.get("conf", 0.0))

        wf.close()

        text = " ".join(all_words).strip()
        avg_confidence = (
            sum(all_confidences) / len(all_confidences)
            if all_confidences
            else 0.0
        )

        return text, avg_confidence

    @staticmethod
    def normalize_text(text):
        """
        Normalize recognized text.

        Adapted from reference project's normalize_text().
        """
        text = text.lower().strip()

        replacements = {
            "stock": "stop",
            "stopp": "stop",
            "stob": "stop",
            "stap": "stop",
        }

        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)

        for char in [".", ",", "!", "?", ":", ";"]:
            text = text.replace(char, "")

        return text.strip()

    @staticmethod
    def is_valid_speech(text):
        """
        Check if recognized text is meaningful (not filler/noise).

        Adapted from reference project's is_valid_speech().
        """
        if not text:
            return False

        text = text.lower().strip()
        words = text.split()

        if not words:
            return False

        if text in config.FALSE_POSITIVE_PHRASES:
            return False

        if all(word in config.FILLER_WORDS for word in words):
            return False

        return True
