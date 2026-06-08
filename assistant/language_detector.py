"""
Dual-Vosk language detector.

Loads both configured Vosk models and runs a short WAV sample through
each recognizer, comparing average word confidence to pick the best language.
"""

import json
import wave
from pathlib import Path
from typing import Tuple

from vosk import Model, KaldiRecognizer

import config


class LanguageDetector:
    def __init__(self):
        self._models = {}

    def _load(self, lang: str) -> Model:
        if lang in self._models:
            return self._models[lang]
        path = config.VOSK_MODEL_PATHS.get(lang)
        if not path:
            raise ValueError(f"No Vosk model configured for '{lang}'")
        print(f"[LANG] Loading Vosk model for {lang}...")
        m = Model(path)
        self._models[lang] = m
        return m

    def detect(self, wav_path: Path) -> Tuple[str, float]:
        """Return (language, confidence) for the provided WAV file."""
        wav_path = Path(wav_path)
        if not wav_path.exists():
            return config.DEFAULT_LANGUAGE, 0.0

        # Read only a short prefix for speed
        with wave.open(str(wav_path), "rb") as wf:
            fr = wf.getframerate()
            frames = int(fr * config.LANG_DETECT_SECONDS)
            data = wf.readframes(frames)

        best_lang = config.DEFAULT_LANGUAGE
        best_conf = 0.0

        for lang in config.SUPPORTED_LANGUAGES:
            model = self._load(lang)
            rec = KaldiRecognizer(model, fr)
            rec.AcceptWaveform(data)
            j = json.loads(rec.Result())
            text = j.get("text", "")
            confs = [float(w.get("conf", 0.0)) for w in j.get("result", [])]
            conf = float(sum(confs) / len(confs)) if confs else 0.0

            # prefer non-empty text with higher confidence
            score = conf if text.strip() else conf * 0.5
            if score > best_conf:
                best_conf = score
                best_lang = lang

        return best_lang, best_conf
