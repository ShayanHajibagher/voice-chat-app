<div align="center">

# 🤖 AI Voice Chat v7

**A fully offline, multi-user voice assistant with a modern web UI — powered by local AI.**

---

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-SHACL%201.0-purple?style=flat-square)](src/LICENSE.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)](#)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)](#)

<hr style="border: 1px solid #6c63ff; width: 60%;">

<p align="center">
  <b>Speak. Type. Listen. All offline. All private.</b><br>
  <i>Multi-user · Encrypted Conversations · Hermes-Inspired Memory · Streaming AI · Persian & English</i>
</p>

</div>

---

## ✨ Features

<table>
<tr>
  <td width="33%" align="center">
    <h3>🎤 <b>Voice & Text</b></h3>
    <p>Speak with your mic or type messages. Real-time VAD, silence detection, and waveform visualization. Seamlessly switch between modes mid-conversation.</p>
  </td>
  <td width="33%" align="center">
    <h3>🧠 <b>AI Streaming</b></h3>
    <p>Token-by-token streaming from any OpenAI-compatible backend (LM Studio, Ollama, vLLM, etc.). No waiting for full responses — read as it thinks.</p>
  </td>
  <td width="33%" align="center">
    <h3>🔐 <b>Encrypted at Rest</b></h3>
    <p>Every conversation file is AES-128-CBC encrypted with HMAC signing (Fernet). The key lives on your machine — conversations are unreadable outside the app.</p>
  </td>
</tr>
<tr>
  <td width="33%" align="center">
    <h3>👥 <b>Multi-User Auth</b></h3>
    <p>Login/signup with salted SHA-256 password hashing. Session tokens validated on every SocketIO connection. Fully isolated data per user.</p>
  </td>
  <td width="33%" align="center">
    <h3>📝 <b>Hermes Memory</b></h3>
    <p>Persistent memory system inspired by the Hermes Agent protocol. Edit MEMORY.md, USER.md, and SOUL.md from the web UI. The AI remembers who you are across sessions.</p>
  </td>
  <td width="33%" align="center">
    <h3>💬 <b>Session Persistence</b></h3>
    <p>Latest conversation auto-restores on reconnect, even after a server restart. Browse, load, rename, or export past conversations from the sidebar.</p>
  </td>
</tr>
<tr>
  <td width="33%" align="center">
    <h3>🌍 <b>Bilingual</b></h3>
    <p>Full support for English and Persian/Farsi — STT, TTS, and AI prompting. Switch instantly from the settings panel. RTL layout auto-adjusts.</p>
  </td>
  <td width="33%" align="center">
    <h3>⚙️ <b>Settings Persist</b></h3>
    <p>Volume, speech speed, and language preferences survive restarts. All settings are saved per-user in <code>user_settings.json</code> and restored on login.</p>
  </td>
  <td width="33%" align="center">
    <h3>🎨 <b>Modern Web UI</b></h3>
    <p>Glassmorphism auth overlay, gradient message bubbles, icon-only hover action buttons, dark/light theme toggle, and real-time VU meter. Fully responsive.</p>
  </td>
</tr>
</table>

---

## 🧱 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Web UI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Auth Overlay │  │   Chat View  │  │  Sidebar (Settings,  │  │
│  │  (Login/Sign) │  │  (Streaming, │  │  Sessions, Memory,   │  │
│  │      up)      │  │  Actions,    │  │  Diagnostics)        │  │
│  └──────┬───────┘  │  Listen)      │  └──────────────────────┘  │
│         │          └──────┬───────┘                             │
│         └─────────────────┼─────────────────────────────────────┘
│                           │ SocketIO (WSS)
└───────────────────────────┼─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Python Backend (Flask)                      │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Auth Manager  │  │  Voice Chat  │  │   Memory Manager     │  │
│  │ • SHA-256+salt│  │  • Vosk STT  │  │  • MEMORY.md read    │  │
│  │ • Token auth  │  │  • Piper TTS │  │  • USER.md + inject  │  │
│  │ • User CRUD   │  │  • AI stream │  │  • SOUL.md persona   │  │
│  └──────┬───────┘  │  • VAD/speech │  └──────────────────────┘  │
│         │          └──────┬───────┘                             │
│  ┌──────┴───────┐         │         ┌──────────────────────┐  │
│  │ Crypto Manager│         │         │   Download Model     │  │
│  │ • Fernet key  │         └─────────│  • Interactive CLI   │  │
│  │ • Encrypt/    │                   │  • Auto-configure    │  │
│  │   Decrypt     │                   │  • Vosk + Piper      │  │
│  └──────────────┘                   └──────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API: OpenAI-compatible (LM Studio, Ollama, vLLM, ...)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (3.12 recommended)
- **Windows** (Linux support via WSL or manual setup)
- ~4GB free disk space (for voice models)
- An **OpenAI-compatible API** running (e.g., [LM Studio](https://lmstudio.ai), [Ollama](https://ollama.ai), or any OpenAI proxy)

### 1️⃣ Install

Double-click **`install.bat`** or run from terminal:

```batch
install.bat
```

This will:
1. Create a Python virtual environment (`.venv/`)
2. Install all Python dependencies (`pip install -r src/requirements.txt`)
3. Launch the interactive model downloader to choose STT and TTS models

### 2️⃣ Start

```batch
start.bat
```

Your browser opens at **`http://localhost:5000`**.

### 3️⃣ Create Account

1. Click **"Create Account"** on the auth overlay
2. Choose a username and password
3. Sign in — the app is ready to use

---

## 🧭 User Guide

### Auth Flow

| Screen | Description |
|--------|-------------|
| **Login** | Enter username/password. Token persists in `localStorage`. |
| **Sign Up** | Create a new account. Passwords are salted + SHA-256 hashed. |
| **Auto-login** | On reconnect, session token re-validates automatically. |
| **Delete Account** | Danger Zone in Settings — enter username, confirms deletion of all data. |

### Chat Interface

- **Mic button** → Records audio, sends via SocketIO for server-side STT
- **Text input** → Send text messages directly to the AI
- **Hybrid** → Type a message, then use voice to continue — same conversation
- **Action buttons** (hover over any AI message):
  - 📋 Copy — copy response to clipboard
  - 🔊 Listen — replay TTS for that message
  - 🔄 Retry — re-generate the last AI response
  - 🗑 Delete — remove that message

### Settings

| Setting | Description |
|---------|-------------|
| **STT Backend** | Choose between Vosk (offline) or Whisper (higher accuracy) |
| **TTS Voice** | Select per-language voice models |
| **Volume** | Master output volume (0.0–2.0, persists across restarts) |
| **Speed** | TTS speech rate (0.50–1.50, persists across restarts) |
| **Language** | Toggle English/Persian (persists, RTL auto-adjust) |
| **API URL** | Endpoint for the AI backend |
| **System Prompt** | Customize the AI's behavior, view/edit the system prompt |

### Memory System

The Hermes-style memory has three files, editable from the Memory tab:

| File | Purpose |
|------|---------|
| **MEMORY.md** | Long-term conversation memory — facts, preferences, past topics |
| **USER.md** | User profile — name, interests, background |
| **SOUL.md** | AI personality — instructions for tone, style, behavior |

The AI reads all three files before generating each response, giving it persistent context across sessions.

---

## 🔐 Security

| Layer | Mechanism |
|-------|-----------|
| **Authentication** | SHA-256 + random salt per user. Tokens expire after 24h. |
| **Session Validation** | Token checked on every SocketIO `connect` event. |
| **Data Isolation** | Each user's data lives in `memories/users/{username}/`. No cross-user access. |
| **Encryption at Rest** | Conversations encrypted with Fernet (AES-128-CBC + HMAC). Key at `memories/.crypto_key`. |
| **Backward Compat** | Encrypted files prefixed with `gAAAAA`; plain files still readable. |
| **Token Storage** | In-memory session store (not cookies). Wiped on server restart. |

---

## 📁 Project Structure

```
voice-chat-ai-v7/
├── 📄 install.bat                  # One-click installer + model downloader
├── 📄 start.bat                    # One-click launcher
├── 📄 .gitignore
├── 📄 README.md
└── 📁 src/
    ├── 📄 web_server.py            # Flask + SocketIO server (entry point)
    ├── 📄 voice_chat.py            # STT, TTS, AI streaming core
    ├── 📄 auth_manager.py          # User accounts, sessions, tokens
    ├── 📄 crypto_manager.py        # Fernet encryption/decryption
    ├── 📄 memory_manager.py        # Hermes memory system
    ├── 📄 download_model.py        # Interactive model downloader
    ├── 📄 config.json              # Global configuration
    ├── 📄 requirements.txt          # Python dependencies
    ├── 📄 LICENSE.md                # SHACL 1.0 license
    ├── 📁 static/
    │   ├── 📄 style.css            # UI styles (dark/light themes)
    │   ├── 📄 script.js            # Client-side logic + SocketIO
    │   └── 📄 manifest.json        # PWA manifest
    ├── 📁 templates/
    │   └── 📄 index.html           # Single-page web UI
    └── 📁 memories/
        ├── 📄 MEMORY.md            # Long-term memory template
        ├── 📄 USER.md              # User profile template
        └── 📄 SOUL.md              # AI personality template
```

---

## 📦 Dependencies

```
faster-whisper     # High-accuracy STT (optional, whisper backend)
vosk               # Offline STT engine
piper-tts          # Local neural TTS
flask              # Web framework
flask-socketio     # Real-time communication
flask-cors         # Cross-origin support
eventlet           # Async WSGI server
cryptography       # Fernet encryption
requests           # API client
```

---

## 🌐 API Compatibility

This app works with any OpenAI-compatible chat completions API:

| Backend | URL |
|---------|-----|
| **LM Studio** | `http://localhost:1234/v1/chat/completions` |
| **Ollama** | `http://localhost:11434/v1/chat/completions` |
| **vLLM** | `http://localhost:8000/v1/chat/completions` |
| **OpenAI** | `https://api.openai.com/v1/chat/completions` |

---

## 📜 License

**SHACL 1.0 — Shayan Hajibagher Attribution-Commercial License**

- ✅ Free for personal, educational, and non-commercial use
- ✅ Modification and distribution permitted with license notice
- 💼 **Commercial use requires attribution** to Shayan Hajibagher

See [`src/LICENSE.md`](src/LICENSE.md) for full terms.

---

<div align="center">

**Built with ❤️ by [Shayan Hajibagher](https://cyandiamondstudio.github.io/website)**  
📧 shayan.contact.email@gmail.com  

<sub>Powered by Cyan Diamond Studio</sub>

</div>
