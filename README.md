<div align="center">

<!-- Animated Hero SVG -->
<svg width="100%" height="180" viewBox="0 0 800 180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f0f13;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1a1a22;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#6c5ce7" />
      <stop offset="100%" style="stop-color:#a29bfe" />
    </linearGradient>
    <linearGradient id="greenGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#00d68f" />
      <stop offset="100%" style="stop-color:#00e676" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="800" height="180" rx="16" fill="url(#bgGrad)" stroke="#333340" stroke-width="1"/>

  <!-- Animated voice waves - left side -->
  <g transform="translate(80, 90)">
    <rect x="0" y="-10" width="6" height="20" rx="3" fill="#6c5ce7" opacity="0.6">
      <animate attributeName="height" values="20;40;20" dur="0.8s" repeatCount="indefinite" begin="0s"/>
      <animate attributeName="y" values="-10;-20;-10" dur="0.8s" repeatCount="indefinite" begin="0s"/>
    </rect>
    <rect x="12" y="-16" width="6" height="32" rx="3" fill="#6c5ce7" opacity="0.7">
      <animate attributeName="height" values="32;50;32" dur="1s" repeatCount="indefinite" begin="0.1s"/>
      <animate attributeName="y" values="-16;-25;-16" dur="1s" repeatCount="indefinite" begin="0.1s"/>
    </rect>
    <rect x="24" y="-20" width="6" height="40" rx="3" fill="#7c6cf7" opacity="0.8">
      <animate attributeName="height" values="40;60;40" dur="0.9s" repeatCount="indefinite" begin="0.2s"/>
      <animate attributeName="y" values="-20;-30;-20" dur="0.9s" repeatCount="indefinite" begin="0.2s"/>
    </rect>
    <rect x="36" y="-24" width="6" height="48" rx="3" fill="#8b7cf7" opacity="0.9">
      <animate attributeName="height" values="48;70;48" dur="1.1s" repeatCount="indefinite" begin="0.3s"/>
      <animate attributeName="y" values="-24;-35;-24" dur="1.1s" repeatCount="indefinite" begin="0.3s"/>
    </rect>
    <rect x="48" y="-22" width="6" height="44" rx="3" fill="#a29bfe" opacity="0.85">
      <animate attributeName="height" values="44;65;44" dur="0.7s" repeatCount="indefinite" begin="0.15s"/>
      <animate attributeName="y" values="-22;-32;-22" dur="0.7s" repeatCount="indefinite" begin="0.15s"/>
    </rect>
    <rect x="60" y="-14" width="6" height="28" rx="3" fill="#b8b2ff" opacity="0.65">
      <animate attributeName="height" values="28;45;28" dur="0.85s" repeatCount="indefinite" begin="0.25s"/>
      <animate attributeName="y" values="-14;-22;-14" dur="0.85s" repeatCount="indefinite" begin="0.25s"/>
    </rect>
  </g>

  <!-- Microphone icon -->
  <g transform="translate(200, 90)">
    <animateTransform attributeName="transform" type="translate" values="200,90;200,88;200,90" dur="2s" repeatCount="indefinite"/>
    <rect x="-10" y="-25" width="20" height="30" rx="10" fill="none" stroke="url(#accentGrad)" stroke-width="3"/>
    <rect x="-3" y="5" width="6" height="12" rx="3" fill="url(#accentGrad)"/>
    <path d="M-15,0 Q-15,25 0,30 Q15,25 15,0" fill="none" stroke="url(#accentGrad)" stroke-width="3"/>
  </g>

  <!-- Title text -->
  <text x="260" y="65" font-family="'Segoe UI', system-ui, sans-serif" font-size="36" font-weight="700" fill="#e8e8ed" letter-spacing="-0.5">AI Voice Chat</text>
  <text x="260" y="95" font-family="'Segoe UI', system-ui, sans-serif" font-size="15" fill="#9898a8">Fully offline voice assistant with web UI</text>

  <!-- Powered by waves - right side -->
  <g transform="translate(640, 90)">
    <rect x="0" y="-14" width="5" height="28" rx="2.5" fill="#00d68f" opacity="0.5">
      <animate attributeName="height" values="28;48;28" dur="1s" repeatCount="indefinite" begin="0.35s"/>
      <animate attributeName="y" values="-14;-24;-14" dur="1s" repeatCount="indefinite" begin="0.35s"/>
    </rect>
    <rect x="10" y="-18" width="5" height="36" rx="2.5" fill="#00d68f" opacity="0.65">
      <animate attributeName="height" values="36;55;36" dur="0.75s" repeatCount="indefinite" begin="0.05s"/>
      <animate attributeName="y" values="-18;-27;-18" dur="0.75s" repeatCount="indefinite" begin="0.05s"/>
    </rect>
    <rect x="20" y="-22" width="5" height="44" rx="2.5" fill="#00d68f" opacity="0.8">
      <animate attributeName="height" values="44;65;44" dur="1.2s" repeatCount="indefinite" begin="0.2s"/>
      <animate attributeName="y" values="-22;-32;-22" dur="1.2s" repeatCount="indefinite" begin="0.2s"/>
    </rect>
    <rect x="30" y="-20" width="5" height="40" rx="2.5" fill="#00e676" opacity="0.7">
      <animate attributeName="height" values="40;58;40" dur="0.95s" repeatCount="indefinite" begin="0.4s"/>
      <animate attributeName="y" values="-20;-29;-20" dur="0.95s" repeatCount="indefinite" begin="0.4s"/>
    </rect>
    <rect x="40" y="-12" width="5" height="24" rx="2.5" fill="#00e676" opacity="0.45">
      <animate attributeName="height" values="24;38;24" dur="0.8s" repeatCount="indefinite" begin="0.1s"/>
      <animate attributeName="y" values="-12;-19;-12" dur="0.8s" repeatCount="indefinite" begin="0.1s"/>
    </rect>
  </g>

  <!-- Bottom decorative line -->
  <line x1="40" y1="155" x2="760" y2="155" stroke="#333340" stroke-width="1" opacity="0.5"/>
  <text x="400" y="170" font-family="'Segoe UI', system-ui, sans-serif" font-size="12" fill="#686878" text-anchor="middle" letter-spacing="2">POWERED BY FASTER-WHISPER · PIPER TTS · FLASK</text>
</svg>

<br>

<!-- Badges -->
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8+-6c5ce7?logo=python&logoColor=white&style=for-the-badge" alt="Python"></a>
<a href="https://github.com/SYANiDE/"><img src="https://img.shields.io/badge/Windows-0078D4?logo=windows&logoColor=white&style=for-the-badge" alt="Windows"></a>
<a href="src/LICENSE.md"><img src="https://img.shields.io/badge/license-SHACL-00d68f?style=for-the-badge" alt="License"></a>
<a href="#"><img src="https://img.shields.io/badge/offline--ready-ffd93d?style=for-the-badge" alt="Offline Ready"></a>

<br><br>

<!-- Animated Subtitle Bar -->
<svg width="600" height="40" viewBox="0 0 600 40" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="600" height="40" rx="20" fill="#252530" stroke="#333340" stroke-width="1"/>
  <circle cx="30" cy="20" r="6" fill="#00d68f">
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  <text x="50" y="25" font-family="'Segoe UI', system-ui, sans-serif" font-size="14" fill="#9898a8">Speak naturally — get AI-powered voice responses, fully offline</text>
</svg>

</div>

---

## Overview

**AI Voice Chat** lets you have natural voice conversations with a local AI model. Speak into your microphone, get transcribed by **faster-whisper**, processed by an **OpenAI-compatible API** (LM Studio, Ollama, etc.), and hear the response spoken aloud via **Piper TTS** — all running **100% locally** on your machine.

<br>

<!-- Animated Features Grid -->
<details open>
<summary><b>Key Features</b></summary>
<br>

<div align="center">

| | Feature | Description |
|:---:|---------|-------------|
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><animateTransform attributeName="transform" type="rotate" values="0 12 12;360 12 12" dur="4s" repeatCount="indefinite"/></svg> | **Web UI** | Modern interface with chat, settings, and stats panels. Dark/light theme. |
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg> | **Dual STT** | faster-whisper (default, best accuracy) with automatic Vosk fallback. |
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><polygon points="11 5 6 9 2 8 14 2 18 6 17 10 11 5"/><polyline points="18 16 20 18 22 16"/><path d="M17 11l-4 4"/><path d="M3 17l4-4"/></svg> | **Piper TTS** | High-quality neural text-to-speech. lessac-high for English, mana-medium for Persian. |
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> | **Multi-language** | English and Persian/Farsi with seamless switching. |
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg> | **Settings panel** | Change STT backend, Whisper model, TTS voice, API URL/key, volume, speed from the browser. |
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> | **Export** | Download your conversation as JSON or plain text. |
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg> | **Session stats** | Track messages, words spoken, and session time. |
| <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> | **Fully offline** | After initial model download, everything runs locally with no internet required. |

</div>
</details>

---

## Quick Start

<div align="center">

| Step | Action | What happens |
|:----:|--------|-------------|
| <span style="font-size:20px">①</span> | **Install** — Run `install.bat` | Creates `.venv`, installs deps, downloads models |
| <span style="font-size:20px">②</span> | **Start** — Run `start.bat` | Starts web server on `http://localhost:5000` |
| <span style="font-size:20px">③</span> | **Speak** — Press mic or <kbd>Space</kbd> | Talk naturally, get AI voice responses |

</div>

### Install

```batch
cd production
install.bat
```

### Start

```batch
cd production
start.bat
```

---

## Manual Installation

```batch
cd production
python -m venv .venv
.venv\Scripts\activate
pip install -r src\requirements.txt
cd src
python download_model.py
python cli.py
```

Start in terminal/CLI mode instead of web UI:

```batch
cd src
python cli.py --cli
```

---

## Screenshots

<div align="center">
  <i>Screenshots coming soon — the chat view, settings panel, and stats dashboard.</i>
</div>

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser (Web UI)                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐    │
│  │    Chat       │   │   Settings    │   │     Stats          │    │
│  │    View       │   │   Panel       │   │     Dashboard      │    │
│  └───────┬───────┘   └──────────────┘   └────────────────────┘    │
│          │                                                         │
│  ┌───────▼─────────────────────────────────────────────────────┐  │
│  │  MediaRecorder → decodeAudioData → encodeWAV                 │  │
│  │  (WebM → PCM → 16kHz WAV)                                   │  │
│  └───────┬─────────────────────────────────────────────────────┘  │
└──────────┼─────────────────────────────────────────────────────────┘
           │ SocketIO (WebSocket)
┌──────────▼─────────────────────────────────────────────────────────┐
│                        Python Server                                │
│  ┌──────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │   flask       │   │  flask-socketio │   │   VoiceChat Core   │   │
│  │ + WebServer  │   │   Events        │   │                    │   │
│  └──────────────┘   └───────┬─────────┘   └────────┬───────────┘   │
│                             │                       │               │
│                        ┌────▼───────────────────────▼───────┐      │
│                        │   process_audio_message()            │      │
│                        │   ┌──────────┐  ┌───────────────┐   │      │
│                        │   │whisper/   │  │  Piper TTS    │   │      │
│                        │   │Vosk STT   │  │  Synthesis    │   │      │
│                        │   └─────┬─────┘  └───────▲───────┘   │      │
│                        │         │                 │           │      │
│                        │    ┌────▼─────────────────┘           │      │
│                        │    │  chat_with_ai()                  │      │
│                        │    │  (HTTP to LM Studio / API)       │      │
│                        │    └─────────────────────────────────  │      │
│                        └────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
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
└── src/
    ├── cli.py               # Entry point (web UI by default, --cli for terminal)
    ├── voice_chat.py         # Core: Whisper+Vosk STT, Piper TTS, AI chat loop
    ├── web_server.py         # Flask + SocketIO server
    ├── download_model.py     # Interactive model downloader
    ├── animations.py         # CLI animations and colors
    ├── window_focus.py       # Window monitoring utility
    ├── config.json           # Configuration file
    ├── requirements.txt      # Python dependencies
    ├── LICENSE.md            # License agreement
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
| <kbd>Space</kbd> | Toggle recording (when chat view is focused) |

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

This project is open source under the **SHACL (Shayan Hajibagher Attribution-Commercial License)**.

<div align="center">
<br>
<svg width="560" height="80" viewBox="0 0 560 80" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="l1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#6c5ce7"/>
      <stop offset="100%" style="stop-color:#00d68f"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="560" height="80" rx="12" fill="#1a1a22" stroke="#333340" stroke-width="1"/>
  <text x="280" y="30" font-family="'Segoe UI', system-ui, sans-serif" font-size="14" fill="#9898a8" text-anchor="middle">Non-commercial use: free — Commercial use: attribution required</text>
  <text x="280" y="60" font-family="'Segoe UI', system-ui, sans-serif" font-size="13" fill="#686878" text-anchor="middle">Any commercial use must name Shayan Hajibagher as the creator of the base project.</text>
</svg>
<br><br>
</div>

See [`src/LICENSE.md`](src/LICENSE.md) for full terms.

> **Powered by Cyan Diamond Studio — AI Voice Chat**

---

## Contact

**Developer:** Shayan Hajibagher  
**Email:** shayan.contact.email@gmail.com  
**Website:** [cyan.diamond.studio](https://cyandiamondstudio.github.io/website/)
