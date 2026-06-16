# AI Voice Chat v6

**Fully offline voice assistant with web UI, powered by faster-whisper and Piper TTS.**

![Python](https://img.shields.io/badge/python-3.8+-blue?logo=python)
![Windows](https://img.shields.io/badge/Windows-0078D4?logo=windows)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## Overview

AI Voice Chat lets you have natural voice conversations with a local AI model. Speak into your microphone, get transcribed by **faster-whisper**, processed by an **OpenAI-compatible API** (LM Studio, Ollama, etc.), and hear the response spoken aloud via **Piper TTS** — all running locally on your machine.

### Key Features

| Feature | Description |
|---------|-------------|
| Web UI | Modern interface with chat, settings, stats panels. Dark/light theme. |
| Dual STT | faster-whisper (default, best accuracy) with automatic Vosk fallback. |
| Piper TTS | High-quality neural text-to-speech. lessac-high for English, mana-medium for Persian. |
| Multi-language | English and Persian/Farsi with seamless switching. |
| Settings panel | Change STT backend, Whisper model, TTS voice, API URL/key, volume, speed from the browser. |
| Conversation export | Download as JSON or plain text. |
| Session stats | Track messages, words spoken, session time. |
| .venv isolation | All dependencies in a virtual environment — no system pollution. |
| Fully offline | After initial model download, everything runs locally with no internet required. |

---

## Quick Start

### 1. Install

Double-click **`install.bat`** (in the `production/` folder):

```batch
cd production
install.bat
```

This will:
- Create a `.venv` virtual environment inside `production/`
- Install Python dependencies (`faster-whisper`, `piper-tts`, `flask`, `flask-socketio`, `vosk`, `pyaudio`, etc.)
- Launch the interactive model downloader to choose your STT and TTS models

### 2. Start

Double-click **`start.bat`** (in the `production/` folder):

```batch
cd production
start.bat
```

This will:
- Activate the virtual environment
- Start the web server on `http://localhost:5000`
- Open your browser automatically

### 3. Speak

Press the microphone button (or press **Space**) and start talking. The AI will respond with text and speech.

---

## Manual Installation

If you prefer to install manually:

```batch
cd production
python -m venv .venv
.venv\Scripts\activate
pip install -r src\requirements.txt
cd src
python download_model.py
python cli.py
```

To start in terminal/CLI mode instead of web UI:

```batch
cd src
python cli.py --cli
```

---

## Screenshots

> *(Add screenshots here — the chat view, settings panel, and stats view)*

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser (Web UI)                   │
│  ┌──────────┐   ┌──────────┐   ┌────────────────┐   │
│  │  Chat     │   │ Settings  │   │   Stats        │   │
│  │  View     │   │  Panel    │   │   Dashboard    │   │
│  └─────┬─────┘   └──────────┘   └────────────────┘   │
│        │                                              │
│  ┌─────▼──────────────────────────────────────────┐   │
│  │  MediaRecorder → decodeAudioData → encodeWAV    │   │
│  │  (WebM → PCM → 16kHz WAV)                      │   │
│  └─────┬──────────────────────────────────────────┘   │
└────────┼──────────────────────────────────────────────┘
         │ SocketIO (WebSocket)
┌────────▼──────────────────────────────────────────────┐
│                   Python Server                        │
│  ┌──────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │ flask      │    │  flask-       │   │  VoiceChat    │  │
│  │ +          │    │  socketio    │   │  Core         │  │
│  │ WebServer  │    │  Events      │   │              │  │
│  └──────────┘    └──────┬───────┘   └──────┬───────┘  │
│                         │                   │          │
│                    ┌────▼───────────────────▼──────┐   │
│                    │  process_audio_message()       │   │
│                    │  ┌──────────┐ ┌────────────┐  │   │
│                    │  │whisper/  │ │  Piper TTS │  │   │
│                    │  │Vosk STT  │ │  Synthesis │  │   │
│                    │  └────┬─────┘ └────▲───────┘  │   │
│                    │       │            │          │   │
│                    │  ┌────▼────────────┘          │   │
│                    │  │  chat_with_ai()            │   │
│                    │  │  (HTTP to LM Studio / API) │   │
│                    │  └─────────────────────────── │   │
│                    └───────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## Configuration

Settings are stored in `src/config.json`:

```json
{
  "language": "en",
  "stt_backend": "whisper",
  "whisper_model": "turbo",
  "languages": {
    "en": {
      "vosk_model_path": "vosk-model-small-en-us-0.15",
      "model_path": "en_US-lessac-high.onnx",
      "config_path": "en_US-lessac-high.onnx.json"
    },
    "fa": {
      "vosk_model_path": "vosk-model-small-fa-rhasspy-0.15",
      "model_path": "fa_IR-mana-medium.onnx",
      "config_path": "fa_IR-mana-medium.onnx.json"
    }
  },
  "api_url": "http://localhost:1234/v1/chat/completions",
  "api_key": "",
  "api_timeout": 120,
  "max_retries": 3,
  "sample_rate": 16000,
  "chunk_size": 8192,
  "max_tokens": 1500,
  "temperature": 0.7,
  "synth": {
    "volume": 1.1,
    "length_scale": 1.05,
    "noise_scale": 0.4,
    "noise_w_scale": 0.5,
    "normalize_audio": true
  }
}
```

| Key | Description |
|-----|-------------|
| `stt_backend` | `"whisper"` or `"vosk"`. Whisper recommended for best accuracy. |
| `whisper_model` | `"turbo"` (default), `"large-v3"`, `"medium"`, `"small"`, `"base"`, `"tiny"` |
| `api_url` | OpenAI-compatible endpoint (e.g. LM Studio at `http://localhost:1234/v1/chat/completions`) |
| `api_key` | Optional Bearer token for authenticated endpoints |
| `language` | Default language: `"en"` or `"fa"` |
| `synth` | TTS parameters — volume, speed, noise scales |

You can also change most settings from the Web UI's **Settings** panel.

---

## Project Structure

```
production/
├── install.bat              # One-click installer
├── start.bat                # One-click launcher
├── .gitignore
├── README.md                # This file
└── src/                     # Source code
    ├── cli.py               # Entry point (web UI by default, --cli for terminal)
    ├── voice_chat.py         # Core: Whisper+Vosk STT, Piper TTS, AI chat loop
    ├── web_server.py         # Flask + SocketIO server
    ├── download_model.py     # Interactive model downloader
    ├── animations.py         # CLI animations and colors
    ├── window_focus.py       # Window monitoring utility
    ├── config.json           # Configuration file
    ├── requirements.txt      # Python dependencies
    ├── LICENSE.md            # License agreement
    ├── .gitignore
    ├── static/
    │   ├── style.css         # Dark/light themed CSS
    │   └── script.js         # SocketIO client, audio recording, waveform
    └── templates/
        └── index.html        # Web UI (chat, settings, stats)
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Toggle recording (when chat view is focused) |
| Click mic button | Record audio |

---

## Dependencies

- **faster-whisper** — State-of-the-art speech recognition (CTranslate2 backend)
- **piper-tts** — Fast neural text-to-speech
- **vosk** — Lightweight offline speech recognition (fallback)
- **Flask** + **Flask-SocketIO** — Web server and real-time communication
- **pyaudio** — Audio capture and playback
- **requests** — HTTP client for AI API calls

---

## License

This project is licensed under a proprietary license by **Cyan Diamond Studio**. See `src/LICENSE.md` for full terms.

Powered by Cyan Diamond Studio — AI Voice Chat

---

## Contact

**Developer:** Shayan Hajibagher  
**Email:** shayan.contact.email@gmail.com  
**Website:** [cyan.diamond.studio](https://cyandiamondstudio.github.io/website/)
