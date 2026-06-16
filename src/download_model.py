import requests
import os
import zipfile
import json


def download_file(url, filename):
    print(f"Downloading {filename}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end="")
        print(f"\nDownloaded {filename}")
        return True
    except Exception as e:
        print(f"\nError downloading {filename}: {e}")
        return False


def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted to {extract_to}")
        return True
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")
        return False


def download_whisper_model(model_name):
    """Pre-download and cache a Whisper model using faster-whisper"""
    print(f"\nDownloading faster-whisper model '{model_name}'...")
    print("This may take a few minutes depending on your internet speed.")
    print()
    try:
        from faster_whisper import WhisperModel
        print(f"Loading WhisperModel({model_name}) — this downloads from HuggingFace Hub if not cached...\n")
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        import numpy as np
        dummy = np.zeros(16000, dtype=np.float32)
        segs, _ = model.transcribe(dummy, language="en")
        list(segs)
        print(f"\nWhisper model '{model_name}' downloaded and cached locally.")
        return True
    except ImportError:
        print("faster-whisper not installed. Install with: pip install faster-whisper")
        return False
    except Exception as e:
        print(f"Failed to download Whisper model: {e}")
        return False


def update_config(stt_backend=None, whisper_model=None, lang=None, vosk_path=None, tts_model=None, tts_config=None):
    if not os.path.exists("config.json"):
        return
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if stt_backend:
        cfg["stt_backend"] = stt_backend
    if whisper_model:
        cfg["whisper_model"] = whisper_model
    if lang and vosk_path:
        cfg["languages"][lang]["vosk_model_path"] = vosk_path
    if lang and tts_model:
        cfg["languages"][lang]["model_path"] = tts_model
    if lang and tts_config:
        cfg["languages"][lang]["config_path"] = tts_config
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print(f"config.json updated")


def download_vosk(model_name):
    base_url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    zip_fn = f"{model_name}.zip"
    print(f"Downloading Vosk model: {model_name}")
    if os.path.exists(model_name):
        if input(f"Model '{model_name}' exists. Redownload? (y/N): ").lower() != "y":
            print("Using existing model.")
            return True
    if not download_file(base_url, zip_fn):
        print(f"Manual: {base_url}")
        return False
    if not extract_zip(zip_fn, "."):
        return False
    os.unlink(zip_fn)
    print(f"Vosk model ready: {model_name}/")
    return True


def download_vosk_fa(model_name):
    base_url = f"https://github.com/rhasspy/fa_kaldi-rhasspy/releases/download/v1.0/{model_name}.zip"
    zip_fn = f"{model_name}.zip"
    print(f"Downloading Vosk model: {model_name}")
    if os.path.exists(model_name):
        if input(f"Model '{model_name}' exists. Redownload? (y/N): ").lower() != "y":
            print("Using existing model.")
            return True
    if not download_file(base_url, zip_fn):
        print(f"Manual: {base_url}")
        return False
    if not extract_zip(zip_fn, "."):
        return False
    os.unlink(zip_fn)
    print(f"Vosk model ready: {model_name}/")
    return True


def download_tts(lang, voice):
    if lang == "en":
        if voice == "lessac-high":
            base = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/high/"
            files = ["en_US-lessac-high.onnx", "en_US-lessac-high.onnx.json"]
        elif voice == "amy-medium":
            base = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/"
            files = ["en_US-amy-medium.onnx", "en_US-amy-medium.onnx.json"]
        elif voice == "ryan-high":
            base = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/"
            files = ["en_US-ryan-high.onnx", "en_US-ryan-high.onnx.json"]
        else:
            print(f"Unknown English voice: {voice}")
            return False
    elif lang == "fa":
        if voice == "mana-medium":
            base = "https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/"
            files = ["fa_IR-mana-medium.onnx", "fa_IR-mana-medium.onnx.json"]
        elif voice == "amir-medium":
            base = "https://huggingface.co/MahtaFetrat/Amir-Persian-Piper/resolve/main/"
            files = ["fa_IR-amir-medium.onnx", "fa_IR-amir-medium.onnx.json"]
        else:
            print(f"Unknown Persian voice: {voice}")
            return False

    print(f"\nDownloading Piper TTS ({voice})...\n")
    ok = True
    for fn in files:
        if os.path.exists(fn):
            print(f"Exists: {fn}")
            continue
        if not download_file(base + fn, fn):
            ok = False
            break
    if ok:
        print("TTS download complete.")
    else:
        print(f"TTS download failed. Manual: {base}")
    return ok


if __name__ == "__main__":
    print("=" * 60)
    print("AI Voice Chat - Model Downloader")
    print("=" * 60)
    print()

    print("Select STT backend:")
    print("1. faster-whisper (turbo) - BEST accuracy, fully offline [recommended]")
    print("2. Vosk - Lightweight, lower accuracy")
    print()

    stt_choice = input("Choice (1-2) or Enter for default (1): ").strip()

    use_whisper = stt_choice not in ("2",)
    whisper_model = "turbo"
    if use_whisper:
        print("\n  Whisper models (from larger/slower to smaller/faster):")
        print("    large-v3  (~3GB)  - Best accuracy, needs GPU")
        print("    medium    (~1.5GB) - Good balance")
        print("    small     (~500MB) - Fast, decent accuracy")
        print("    base      (~150MB) - Faster")
        print("    tiny      (~75MB)  - Fastest")
        print("    turbo     (~800MB) - Optimized for speed [recommended]")
        print()
        w_choice = input("Enter model name or Enter for turbo: ").strip()
        whisper_model = w_choice if w_choice else "turbo"

        print()
        print(f"Pre-downloading Whisper model '{whisper_model}'...")
        print("(Only needed once — cached for future use)")
        if not download_whisper_model(whisper_model):
            print("\nFalling back to Vosk STT.")
            use_whisper = False

    print()
    print("Select language:")
    print("1. English")
    print("2. Persian")
    print("3. Both")
    print()
    lang_choice = input("Choice (1-3) or Enter for English (1): ").strip()

    lang_map = {"1": ["en"], "2": ["fa"], "3": ["en", "fa"], "": ["en"]}
    languages = lang_map.get(lang_choice, ["en"])

    print()

    for lang in languages:
        print("-" * 60)
        print(f"  Language: {lang.upper()}")
        print("-" * 60)

        vosk_ok = True
        vosk_selected = None

        if not use_whisper:
            if lang == "en":
                print("\nVosk models:")
                print("1. vosk-model-small-en-us-0.15 (~40MB) [recommended]")
                print("2. vosk-model-en-us-0.22 (~1.8GB) - Best accuracy")
                print("3. vosk-model-tiny-en-us-0.15 (~40MB) - Fastest")
                c = input("\nChoice (1-3) or Enter for default (1): ").strip()
                m = {"1": "vosk-model-small-en-us-0.15", "2": "vosk-model-en-us-0.22", "3": "vosk-model-tiny-en-us-0.15", "": "vosk-model-small-en-us-0.15"}
                vosk_selected = m.get(c, "vosk-model-small-en-us-0.15")
                print("\nDownloading Vosk model...")
                vosk_ok = download_vosk(vosk_selected)
            else:
                vosk_selected = "vosk-model-small-fa-rhasspy-0.15"
                print("\nDownloading Vosk Persian model...")
                vosk_ok = download_vosk_fa(vosk_selected)

        print()
        print("TTS voice selection:")
        if lang == "en":
            print("1. en_US-lessac-high (~100MB) - BEST quality [recommended]")
            print("2. en_US-amy-medium (~61MB) - Medium quality")
            print("3. en_US-ryan-high (~185MB) - Premium high quality")
            c = input("\nChoice (1-3) or Enter for default (1): ").strip()
            tts_map = {"1": "lessac-high", "2": "amy-medium", "3": "ryan-high", "": "lessac-high"}
            tts_voice = tts_map.get(c, "lessac-high")
        else:
            print("1. fa_IR-mana-medium (~60MB) [recommended]")
            print("2. fa_IR-amir-medium (~60MB)")
            c = input("\nChoice (1-2) or Enter for default (1): ").strip()
            tts_map = {"1": "mana-medium", "2": "amir-medium", "": "mana-medium"}
            tts_voice = tts_map.get(c, "mana-medium")

        tts_file = f"{lang.upper()}_{tts_voice.replace('-', '_')}.onnx"
        if lang == "en":
            tts_file = f"en_US-{tts_voice}.onnx"
            tts_cfg = f"en_US-{tts_voice}.onnx.json"
        else:
            tts_file = f"fa_IR-{tts_voice}.onnx"
            tts_cfg = f"fa_IR-{tts_voice}.onnx.json"

        print(f"\nDownloading TTS ({tts_voice})...")
        tts_exists = os.path.exists(tts_file)
        if tts_exists:
            print(f"TTS model exists ({tts_file}), skipping.")
            tts_ok = True
        else:
            tts_ok = download_tts(lang, tts_voice)

        if vosk_ok and tts_ok:
            update_config(
                stt_backend="whisper" if use_whisper else "vosk",
                whisper_model=whisper_model if use_whisper else None,
                lang=lang,
                vosk_path=vosk_selected,
                tts_model=tts_file,
                tts_config=tts_cfg,
            )
        else:
            print(f"Some downloads failed for {lang}.")

    print()
    print("=" * 60)
    print("Done! All models downloaded and cached.")
    print()
    if use_whisper:
        print(f"  STT:   faster-whisper ({whisper_model}) — cached, zero network on next run")
    for lang in languages:
        tts = "lessac-high" if lang == "en" else "mana-medium"
        print(f"  TTS:   {lang.upper()} — {tts}")
    print()
    print("To start: start.bat  or  python cli.py")
    print("=" * 60)
