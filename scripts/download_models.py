"""
Download all required models and binaries for the Offline Speech Assistant.

Downloads:
  - Piper TTS binary (Windows amd64)
  - Piper voice models (English + German)
  - Triggers faster-whisper model cache
  - Triggers Silero VAD model cache

Usage:
    python scripts/download_models.py
"""

import os
import sys
import io
import zipfile
import shutil
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def download_file(url: str, dest: Path, description: str = "") -> None:
    """Download a file with a progress bar."""
    if dest.exists():
        print(f"  [OK] Already exists: {dest.name}")
        return

    print(f"  [>>] Downloading: {description or dest.name}")
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(
        total=total_size, unit="B", unit_scale=True, desc=dest.name
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))


def download_piper_binary() -> None:
    """Download and extract the Piper TTS binary for Windows."""
    print("\n[1/4] Piper TTS Binary")
    print("-" * 40)

    if config.PIPER_BINARY.exists():
        print(f"  [OK] Already exists: {config.PIPER_BINARY}")
        return

    zip_path = config.PIPER_DIR / "piper_windows_amd64.zip"
    download_file(config.PIPER_BINARY_URL, zip_path, "Piper Windows binary")

    # Extract
    print("  [..] Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(config.PIPER_DIR)

    # The zip extracts into a subdirectory — move contents up
    extracted_dir = config.PIPER_DIR / "piper"
    if extracted_dir.exists():
        for item in extracted_dir.iterdir():
            target = config.PIPER_DIR / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
        shutil.rmtree(extracted_dir)

    # Clean up zip
    zip_path.unlink(missing_ok=True)

    if config.PIPER_BINARY.exists():
        print(f"  [OK] Piper binary ready: {config.PIPER_BINARY}")
    else:
        print("  [!!] ERROR: piper.exe not found after extraction!")
        print(f"    Contents of {config.PIPER_DIR}:")
        for f in config.PIPER_DIR.iterdir():
            print(f"      {f.name}")


def download_piper_voices() -> None:
    """Download Piper voice models for English and German."""
    print("\n[2/4] Piper Voice Models")
    print("-" * 40)

    for lang, urls in config.PIPER_MODEL_URLS.items():
        lang_label = {"en": "English (US)", "de": "German (DE)"}[lang]
        print(f"\n  [{lang_label}]")

        # Download .onnx model
        onnx_name = urls["onnx"].split("/")[-1]
        onnx_path = config.MODELS_DIR / onnx_name
        download_file(urls["onnx"], onnx_path, f"{lang_label} model")

        # Download .onnx.json config
        json_name = urls["json"].split("/")[-1]
        json_path = config.MODELS_DIR / json_name
        download_file(urls["json"], json_path, f"{lang_label} config")


def cache_whisper_model() -> None:
    """Pre-download the faster-whisper model."""
    print(f"\n[3/4] faster-whisper Model ({config.WHISPER_MODEL_SIZE})")
    print("-" * 40)

    try:
        from faster_whisper import WhisperModel

        print("  [>>] Loading model (will download if not cached)...")
        _model = WhisperModel(
            config.WHISPER_MODEL_SIZE,
            device="cpu",  # Use CPU for download to avoid CUDA issues
            compute_type="int8",
        )
        del _model
        print("  [OK] faster-whisper model cached")
    except ImportError:
        print("  [!!] faster-whisper not installed yet. Run: pip install faster-whisper")
    except Exception as e:
        print(f"  [!!] Could not pre-cache model: {e}")
        print("    It will be downloaded on first run.")


def cache_silero_vad() -> None:
    """Pre-download the Silero VAD model."""
    print("\n[4/4] Silero VAD Model")
    print("-" * 40)

    try:
        import torch

        print("  [>>] Loading model via torch.hub...")
        _model, _utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
        )
        del _model, _utils
        print("  [OK] Silero VAD model cached")
    except ImportError:
        print("  [!!] torch not installed yet. Run: pip install torch")
    except Exception as e:
        print(f"  [!!] Could not pre-cache VAD model: {e}")
        print("    It will be downloaded on first run.")


def main() -> None:
    print("=" * 50)
    print("  Offline Speech Assistant -- Model Setup")
    print("=" * 50)

    download_piper_binary()
    download_piper_voices()
    cache_whisper_model()
    cache_silero_vad()

    print("\n" + "=" * 50)
    print("  Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("  1. Make sure Ollama is running:  ollama serve")
    print(f"  2. Pull the LLM model:          ollama pull {config.OLLAMA_MODEL}")
    print("  3. Run the assistant:            python main.py")


if __name__ == "__main__":
    main()
