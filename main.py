"""
Offline Speech Assistant -- Main Entry Point (Raspberry Pi 5)

Pipeline:
  Microphone -> RMS VAD -> Vosk STT (EN + DE) -> Ollama LLM -> Piper TTS -> Speaker
"""

import sys
import io
import signal

# Fix console encoding for Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import config
from assistant.audio_capture import AudioCapture
from assistant.transcriber import Transcriber
from assistant.language_detector import LanguageDetector
from assistant.llm_client import LLMClient
from assistant.tts_engine import TTSEngine


# Language display names
LANG_NAMES = {"en": "English", "de": "Deutsch"}


def normalize_text(text: str) -> str:
    """Normalize transcribed text — lowercase, fix common Vosk mis-hearings."""
    text = text.lower().strip()

    replacements = {
        "stock": "stop",
        "stopp": "stop",
        "stob": "stop",
        "stap": "stop",
        "tschüs": "tschüss",
    }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    for char in [".", ",", "!", "?", ":", ";"]:
        text = text.replace(char, "")

    return text.strip()


def is_valid_speech(text: str) -> bool:
    """Filter false-positive transcriptions (filler words, noise artefacts)."""
    if not text:
        return False

    normalized = normalize_text(text)
    words = normalized.split()

    if not words:
        return False

    if normalized in config.FALSE_POSITIVE_PHRASES:
        return False

    if all(word in config.FILLER_WORDS for word in words):
        return False

    return True


def print_banner() -> None:
    """Display the startup banner."""
    print()
    print("=" * 52)
    print("       Offline Speech Assistant")
    print()
    print("  Vosk + Ollama + Piper -- 100% Offline")
    print("  Languages: English | Deutsch")
    print("  Platform:  Raspberry Pi 5")
    print("=" * 52)
    print()


def main() -> None:
    print_banner()

    # -- Initialize components -----------------------------------------------
    print("[..] Initializing components...\n")

    audio_capture = AudioCapture()
    transcriber = Transcriber()
    lang_detector = LanguageDetector(transcriber)

    llm = LLMClient()

    try:
        tts = TTSEngine()
    except FileNotFoundError as e:
        print(f"[!!] {e}")
        sys.exit(1)

    # -- Graceful shutdown ---------------------------------------------------
    def shutdown(sig=None, frame=None):
        print("\n\n[>>] Shutting down...")
        audio_capture.cleanup()
        print("   Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # -- Main loop -----------------------------------------------------------
    print("\n" + "-" * 52)
    print("[OK] Ready! Speak into your microphone...")
    print("   Press Ctrl+C to exit")
    print("   Say 'reset' to clear conversation")
    print("-" * 52 + "\n")

    while True:
        try:
            # 1. Listen for speech (RMS-based VAD, writes WAV)
            wav_path = audio_capture.listen_for_speech()
            if wav_path is None:
                continue

            # 2. Detect language (dual-Vosk confidence comparison)
            language, confidence = lang_detector.detect(wav_path)
            lang_display = LANG_NAMES.get(language, language)
            print(f"[LANG] {lang_display} ({confidence:.0%})")

            # 3. Transcribe speech to text (Vosk)
            text = transcriber.transcribe_wav(str(wav_path), language)

            # 4. Validate speech (filter noise / filler words)
            if not is_valid_speech(text):
                if text:
                    print(f"  (ignored: {text})")
                else:
                    print("  (no speech recognized)")
                continue

            print(f"[YOU]  {text}")

            # 5. Check for commands
            text_lower = normalize_text(text)
            if text_lower in ("reset", "zurücksetzen", "reset conversation"):
                llm.reset_conversation()
                continue
            if text_lower in ("exit", "quit", "beenden", "stop"):
                shutdown()

            # 6. Get LLM response
            print("[..]  Thinking...")
            response = llm.chat(text, language)
            print(f"[BOT] {response}")

            # 7. Synthesize and play response (Piper -> aplay)
            tts.speak(response, language)

            # Remove the recorded input WAV
            try:
                wav_path.unlink(missing_ok=True)
            except Exception:
                pass

            print()  # Visual separator between turns

        except KeyboardInterrupt:
            shutdown()
        except Exception as e:
            print(f"\n  [!!] Error: {e}")
            print("  Continuing to listen...\n")
            continue


if __name__ == "__main__":
    main()
