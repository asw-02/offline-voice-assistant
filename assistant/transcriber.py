"""
Vosk-based speech-to-text transcriber.

Provides a small wrapper to transcribe WAV files with a given Vosk model.
"""

import json
import wave
from pathlib import Path
from typing import Tuple

from vosk import Model, KaldiRecognizer

import config


class Transcriber:
    """Load Vosk models on demand and transcribe WAV files."""

    def __init__(self):
        # cache for loaded models
        self._models: dict[str, Model] = {}

    def _load_model(self, lang: str) -> Model:
        if lang in self._models:
            return self._models[lang]
        path = config.VOSK_MODEL_PATHS.get(lang)
        if not path:
            raise ValueError(f"No Vosk model configured for language '{lang}'")
        print(f"[STT] Loading Vosk model for {lang} from {path}...")
        model = Model(path)
        self._models[lang] = model
        return model

    def transcribe(self, wav_path: Path, language: str) -> Tuple[str, str, float]:
        """Transcribe a WAV file using the Vosk model for `language`.

        Returns (text, language, confidence)
        """
        wav_path = Path(wav_path)
        if not wav_path.exists():
            return "", language, 0.0

        model = self._load_model(language)
        wf = wave.open(str(wav_path), "rb")
        rec = KaldiRecognizer(model, wf.getframerate())

        results = []
        confidences = []

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                j = json.loads(rec.Result())
                results.append(j.get("text", ""))
                for w in j.get("result", []):
                    confidences.append(float(w.get("conf", 0.0)))
            else:
                # partial = rec.PartialResult()  # ignored for now
                pass

        # final
        j = json.loads(rec.FinalResult())
        results.append(j.get("text", ""))
        for w in j.get("result", []):
            confidences.append(float(w.get("conf", 0.0)))

        text = " ".join(r for r in results if r).strip()
        confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0

        return text, language, confidence
