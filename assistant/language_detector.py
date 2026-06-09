#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Language detection using dual Vosk models.

Since Vosk has no built-in language detection, this module runs
a short audio sample through both the English and German models
and picks the one with higher word-level confidence.
"""

from pathlib import Path

import config


class LanguageDetector:
    """Detects spoken language by comparing Vosk model confidence scores."""

    def __init__(self, transcriber):
        """
        Args:
            transcriber: A Transcriber instance (shared, provides model loading).
        """
        self._transcriber = transcriber
        self._last_language = config.DEFAULT_LANGUAGE

        # Pre-load both models
        print("[LANG] Loading language detection models...")
        for lang in config.SUPPORTED_LANGUAGES:
            try:
                self._transcriber.load_model(lang)
            except FileNotFoundError as e:
                print(f"  [!!] {e}")

        print("  [OK] Language detection ready")

    def detect(self, wav_path=config.OUTPUT_WAV):
        """
        Detect the language of a recorded WAV file.

        Runs the audio through both EN and DE Vosk models and
        compares average word-level confidence scores.

        Args:
            wav_path: Path to the WAV file to analyze.

        Returns:
            Tuple of (language_code, confidence).
        """
        if not Path(wav_path).exists():
            return self._last_language, 0.0

        results = {}

        for lang in config.SUPPORTED_LANGUAGES:
            try:
                text, confidence = self._transcriber.transcribe_wav_with_confidence(
                    wav_path, lang
                )
                results[lang] = {
                    "text": text,
                    "confidence": confidence,
                    "word_count": len(text.split()) if text else 0,
                }
            except Exception as exc:
                print(f"  [!!] Language detection error for '{lang}': {exc}")
                results[lang] = {"text": "", "confidence": 0.0, "word_count": 0}

        # Pick the language with the best combination of confidence and word count
        best_lang = self._last_language
        best_score = -1.0

        for lang, result in results.items():
            # Score = confidence * word_count_factor
            # More recognized words with high confidence = better match
            word_factor = min(result["word_count"] / 3.0, 1.0)  # Cap at 3 words
            score = result["confidence"] * (0.5 + 0.5 * word_factor)

            if score > best_score and result["text"]:
                best_score = score
                best_lang = lang

        self._last_language = best_lang

        best_conf = results.get(best_lang, {}).get("confidence", 0.0)
        return best_lang, best_conf

    def detect_with_details(self, wav_path=config.OUTPUT_WAV):
        """
        Detect language with full details for debugging.

        Returns:
            Dictionary with per-language results.
        """
        results = {}

        for lang in config.SUPPORTED_LANGUAGES:
            try:
                text, confidence = self._transcriber.transcribe_wav_with_confidence(
                    wav_path, lang
                )
                results[lang] = {
                    "text": text,
                    "confidence": confidence,
                    "word_count": len(text.split()) if text else 0,
                }
            except Exception:
                results[lang] = {"text": "", "confidence": 0.0, "word_count": 0}

        return results

    @property
    def last_language(self):
        """Return the last detected language."""
        return self._last_language
