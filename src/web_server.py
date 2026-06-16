import os
import json
import base64
import io
import wave
import tempfile
import logging
import subprocess
import time
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from voice_chat import VoiceChat, VoiceChatConfig

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(16).hex()
socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=25, ping_timeout=60)


class WebVoiceChat:
    def __init__(self):
        self.config_path = "config.json"
        self.load_config()

    def load_config(self):
        self.config = VoiceChatConfig(self.config_path)
        # Web mode: never prompt stdin — always start fresh
        self.voice_chat = VoiceChat(self.config, conversation_options={"fresh": True})

    def process_audio(self, audio_base64, sid):
        try:
            emit("status", {"mode": "processing"}, room=sid)
            audio_bytes = base64.b64decode(audio_base64)
            result = self.voice_chat.process_audio_message(audio_bytes)

            if result.get("text"):
                audio_b64 = None
                if result.get("audio"):
                    audio_b64 = base64.b64encode(result["audio"]).decode("utf-8")
                emit("response", {
                    "user_text": result.get("user_text", ""),
                    "text": result["text"],
                    "audio": audio_b64,
                }, room=sid)

            self._send_conversation(sid)
            self._send_status(sid)
        except Exception as e:
            logger.error(f"Process audio error: {e}")
            emit("error", {"message": str(e)}, room=sid)

    def _send_conversation(self, sid):
        emit("conversation", {
            "messages": self.voice_chat.get_conversation_history()
        }, room=sid)

    def _send_status(self, sid=None):
        elapsed = int(self.voice_chat.conversation_stats.get("start_time", 0))
        if elapsed:
            elapsed = int(time.time()) - elapsed
        lang_cfg = self.config.languages.get(self.voice_chat.current_language, {})
        status = {
            "language": self.voice_chat.current_language,
            "volume": self.voice_chat.current_volume,
            "speed": self.voice_chat.current_speed,
            "paused": self.voice_chat.paused,
            "mode": "idle",
            "stats": {
                "user_messages": self.voice_chat.conversation_stats.get("user_messages", 0),
                "ai_messages": self.voice_chat.conversation_stats.get("ai_messages", 0),
                "words_spoken": self.voice_chat.conversation_stats.get("words_spoken", 0),
                "elapsed": elapsed,
            },
        }
        if sid:
            emit("status", status, room=sid)
        else:
            emit("status", status)

    def _send_config(self, sid=None):
        cfg = {
            "stt_backend": getattr(self.config, "stt_backend", "whisper"),
            "whisper_model": getattr(self.config, "whisper_model", "turbo"),
            "api_url": getattr(self.config, "api_url", ""),
            "api_key": getattr(self.config, "api_key", ""),
            "language": self.voice_chat.current_language,
            "tts_voices": {
                lang: {
                    "model_path": info.get("model_path", ""),
                    "config_path": info.get("config_path", ""),
                }
                for lang, info in self.config.languages.items()
            },
        }
        if sid:
            emit("config", cfg, room=sid)
        else:
            emit("config", cfg)

    def _save_config_field(self, key, value):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data[key] = value
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
        return False

    def get_conversation_json(self):
        return json.dumps(self.voice_chat.get_conversation_history(), indent=2, ensure_ascii=False)

    def get_conversation_text(self):
        lines = []
        for msg in self.voice_chat.get_conversation_history():
            role = "You" if msg["role"] == "user" else "AI"
            lines.append(f"[{role}]")
            lines.append(msg["content"])
            lines.append("")
        return "\n".join(lines)


web_chat = WebVoiceChat()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/export/json")
def export_json():
    return web_chat.get_conversation_json(), 200, {"Content-Type": "application/json", "Content-Disposition": "attachment; filename=conversation.json"}


@app.route("/export/text")
def export_text():
    return web_chat.get_conversation_text(), 200, {"Content-Type": "text/plain; charset=utf-8", "Content-Disposition": "attachment; filename=conversation.txt"}


@socketio.on("connect")
def on_connect():
    web_chat._send_status(request.sid)
    web_chat._send_conversation(request.sid)
    web_chat._send_config(request.sid)


@socketio.on("disconnect")
def on_disconnect():
    pass


@socketio.on("audio")
def on_audio(data):
    web_chat.process_audio(data.get("audio", ""), request.sid)


@socketio.on("command")
def on_command(data):
    cmd = data.get("command")

    if cmd == "pause":
        web_chat.voice_chat.pause()
    elif cmd == "resume":
        web_chat.voice_chat.resume()
    elif cmd == "clear":
        web_chat.voice_chat.clear_conversation_history()
        web_chat._send_conversation(request.sid)
    elif cmd == "new":
        web_chat.voice_chat.clear_conversation_history()
        web_chat._send_conversation(request.sid)
    elif cmd == "save":
        web_chat.voice_chat.save_conversation(silent=True)
    elif cmd == "language":
        lang = data.get("language")
        if lang and web_chat.voice_chat.switch_language(lang):
            web_chat._save_config_field("language", lang)
            web_chat._send_config()

    elif cmd == "set_api_url":
        val = data.get("value", "")
        web_chat.voice_chat.config.api_url = val
        web_chat.config.api_url = val
        web_chat._save_config_field("api_url", val)

    elif cmd == "set_api_key":
        val = data.get("value", "")
        web_chat.voice_chat.config.api_key = val
        web_chat.config.api_key = val
        web_chat._save_config_field("api_key", val)

    elif cmd == "set_stt_backend":
        val = data.get("value", "whisper")
        web_chat.voice_chat.config.stt_backend = val
        web_chat.config.stt_backend = val
        web_chat._save_config_field("stt_backend", val)
        web_chat._send_config()
        emit("notify", {"message": "STT backend saved. Restart required to take effect.", "type": "warning"})

    elif cmd == "set_whisper_model":
        val = data.get("value", "turbo")
        web_chat.voice_chat.config.whisper_model = val
        web_chat.config.whisper_model = val
        web_chat._save_config_field("whisper_model", val)
        web_chat._send_config()
        emit("notify", {"message": "Whisper model saved. Restart required to take effect.", "type": "warning"})

    elif cmd == "set_tts_voice":
        lang = data.get("lang")
        model_path = data.get("model_path", "")
        config_path = data.get("config_path", "")
        if lang and lang in web_chat.config.languages:
            web_chat.config.languages[lang]["model_path"] = model_path
            web_chat.config.languages[lang]["config_path"] = config_path
            try:
                if os.path.exists(web_chat.config_path):
                    with open(web_chat.config_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    cfg_data["languages"][lang]["model_path"] = model_path
                    cfg_data["languages"][lang]["config_path"] = config_path
                    with open(web_chat.config_path, "w", encoding="utf-8") as f:
                        json.dump(cfg_data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save TTS config: {e}")
            web_chat._send_config()
            emit("notify", {"message": "TTS voice saved. Restart required.", "type": "warning"})

    elif cmd == "download_models":
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_model.py")
        if os.path.exists(script):
            subprocess.Popen(["python", script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            emit("notify", {"message": "Model downloader opened in a new window.", "type": "info"})
        else:
            emit("notify", {"message": "download_model.py not found!", "type": "error"})

    elif cmd == "volume":
        val = max(0.1, min(2.0, float(data.get("value", 1.0))))
        web_chat.voice_chat.current_volume = val
        web_chat.voice_chat.synth_config.volume = val

    elif cmd == "speed":
        val = max(0.5, min(2.0, float(data.get("value", 1.0))))
        web_chat.voice_chat.current_speed = val
        web_chat.voice_chat.synth_config.length_scale = val

    web_chat._send_status()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
