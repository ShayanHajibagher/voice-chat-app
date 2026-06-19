import os
import json
import base64
import logging
import subprocess
import time
import uuid
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from voice_chat import VoiceChat, VoiceChatConfig
from memory_manager import MemoryManager
from auth_manager import create_user, verify_user, create_session, validate_session, delete_session, delete_user, get_user_dir

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(16).hex()
socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=25, ping_timeout=60)

sessions = {}
sessions_lock = threading_lock = None
import threading
sessions_lock = threading.Lock()


def get_or_create_session(sid):
    with sessions_lock:
        if sid in sessions:
            return sessions[sid]
    return None


def create_user_session(sid, username):
    with sessions_lock:
        config = VoiceChatConfig()
        vc = VoiceChat(config, conversation_options={"fresh": True}, username=username)
        vc.conversation_id = str(uuid.uuid4())[:8]
        sessions[sid] = {"username": username, "voice_chat": vc}
        return vc


def cleanup_session(sid):
    with sessions_lock:
        if sid in sessions:
            vc = sessions[sid]["voice_chat"]
            vc.save_conversation()
            vc._save_user_settings()
            del sessions[sid]


def cleanup_all_sessions(username):
    with sessions_lock:
        to_delete = [sid for sid, s in list(sessions.items()) if s["username"] == username]
        for sid in to_delete:
            vc = sessions[sid]["voice_chat"]
            vc.save_conversation()
            del sessions[sid]


# ---- Auth Routes ----


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"})
    if verify_user(username, password):
        token = create_session(username)
        return jsonify({"success": True, "token": token, "username": username})
    return jsonify({"success": False, "error": "Invalid username or password"})


@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"})
    success, msg = create_user(username, password)
    if success:
        token = create_session(username)
        return jsonify({"success": True, "token": token, "username": username})
    return jsonify({"success": False, "error": msg})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    data = request.get_json() or {}
    token = data.get("token", "")
    delete_session(token)
    return jsonify({"success": True})


@app.route("/api/delete-account", methods=["POST"])
def api_delete_account():
    data = request.get_json() or {}
    token = data.get("token", "")
    username = validate_session(token)
    if not username:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    if username != data.get("username", ""):
        return jsonify({"success": False, "error": "Username mismatch"}), 403
    cleanup_all_sessions(username)
    delete_user(username)
    return jsonify({"success": True})


@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.get_json() or {}
    token = data.get("token", "")
    username = validate_session(token)
    if username:
        return jsonify({"success": True, "username": username})
    return jsonify({"success": False})


# ---- Main Page ----


@app.route("/")
def index():
    return render_template("index.html")


# ---- Export Routes ----


def _get_conversation_path(username, conv_id):
    return os.path.join(get_user_dir(username), "CONVERSATIONS", f"{conv_id}.json")


def _get_conversation_messages(username, conv_id):
    path = _get_conversation_path(username, conv_id)
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                raw = f.read()
            if raw.startswith(b"gAAAAA"):
                from crypto_manager import decrypt_blob
                raw = decrypt_blob(raw)
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return []
    return []


@app.route("/export/json")
def export_json():
    username = request.args.get("user", "default")
    conv_id = request.args.get("id", "default")
    messages = _get_conversation_messages(username, conv_id)
    return json.dumps(messages, indent=2, ensure_ascii=False), 200, {
        "Content-Type": "application/json",
        "Content-Disposition": f"attachment; filename=conversation-{conv_id}.json",
    }


@app.route("/export/text")
def export_text():
    username = request.args.get("user", "default")
    conv_id = request.args.get("id", "default")
    messages = _get_conversation_messages(username, conv_id)
    lines = []
    for msg in messages:
        role = "You" if msg["role"] == "user" else "AI"
        lines.append(f"[{role}]")
        lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines), 200, {
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Disposition": f"attachment; filename=conversation-{conv_id}.txt",
    }


@app.route("/export/markdown")
def export_markdown():
    username = request.args.get("user", "default")
    conv_id = request.args.get("id", "default")
    messages = _get_conversation_messages(username, conv_id)
    lines = []
    for msg in messages:
        role = "**You**" if msg["role"] == "user" else "**AI Assistant**"
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(msg.get("timestamp", 0)))
        lines.append(f"### {role} _{ts}_")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines), 200, {
        "Content-Type": "text/markdown; charset=utf-8",
        "Content-Disposition": f"attachment; filename=conversation-{conv_id}.md",
    }


# ---- Diagnostics ----


@app.route("/api/diagnostics")
def api_diagnostics():
    token = request.headers.get("X-Auth-Token", "")
    username = validate_session(token)
    if not username:
        return jsonify({"error": "Not authenticated"}), 401

    config = VoiceChatConfig()
    results = {}
    stt_available = False
    if config.stt_backend == "whisper":
        try:
            from faster_whisper import WhisperModel
            stt_available = True
        except ImportError:
            stt_available = False
    else:
        stt_available = os.path.exists(config.vosk_model_path)
    tts_available = os.path.exists(config.model_path) and os.path.exists(config.config_path)
    vosk_available = os.path.exists(config.vosk_model_path)
    results["stt"] = {"backend": config.stt_backend, "available": stt_available, "model": config.whisper_model if config.stt_backend == "whisper" else config.vosk_model_path}
    results["tts"] = {"available": tts_available, "model": config.model_path}
    results["vosk"] = {"available": vosk_available, "model": config.vosk_model_path}
    api_ok = False
    api_msg = ""
    try:
        import requests
        r = requests.get(config.api_url.rsplit("/v1/", 1)[0] + "/v1/models", timeout=5)
        api_ok = r.status_code == 200
        api_msg = "Reachable" if api_ok else f"HTTP {r.status_code}"
    except Exception as e:
        api_msg = str(e)[:100]
    results["api"] = {"available": api_ok, "url": config.api_url, "message": api_msg}
    results["languages"] = list(config.languages.keys())
    results["current_language"] = config.language
    mm = MemoryManager(username)
    results["memory"] = {
        "memory_entries": len(mm.load_memory("memory")),
        "user_entries": len(mm.load_memory("user")),
    }
    results["user"] = username
    return jsonify(results)


@app.route("/api/config")
def api_config():
    config = VoiceChatConfig()
    cfg = config.to_dict()
    token = request.headers.get("X-Auth-Token", "")
    username = validate_session(token)
    if username:
        cfg["username"] = username
    return jsonify(cfg)


# ---- SocketIO Events ----


@socketio.on("connect")
def on_connect(auth):
    sid = request.sid
    token = auth.get("token") if auth else None
    username = validate_session(token) if token else None
    if not username:
        return False
    vc = create_user_session(sid, username)
    _send_status(sid)
    _send_conversation(sid)
    _send_config(sid)
    emit("auth_ok", {"username": username}, room=sid)


@socketio.on("disconnect")
def on_disconnect():
    cleanup_session(request.sid)


@socketio.on("audio")
def on_audio(data):
    sid = request.sid
    session = get_or_create_session(sid)
    if not session:
        return
    vc = session["voice_chat"]
    try:
        emit("status", {"mode": "processing"}, room=sid)
        audio_bytes = base64.b64decode(data.get("audio", ""))
        result = vc.process_audio_message(audio_bytes)
        if result.get("text"):
            audio_b64 = None
            if result.get("audio"):
                audio_b64 = base64.b64encode(result["audio"]).decode("utf-8")
            emit("response", {
                "user_text": result.get("user_text", ""),
                "text": result["text"],
                "audio": audio_b64,
            }, room=sid)
        _send_conversation(sid)
        _send_status(sid)
    except Exception as e:
        logger.error(f"Process audio error: {e}")
        emit("error", {"message": str(e)}, room=sid)


@socketio.on("text_message")
def on_text_message(data):
    sid = request.sid
    session = get_or_create_session(sid)
    if not session:
        return
    vc = session["voice_chat"]
    try:
        text = data.get("text", "").strip()
        if not text:
            return
        emit("status", {"mode": "processing"}, room=sid)
        emit("user_text", {"text": text}, room=sid)
        vc.add_to_conversation("user", text)
        if data.get("stream", True):
            full_response = ""
            for chunk, is_done in vc.chat_with_ai_stream(text):
                if not is_done:
                    full_response += chunk
                emit("stream_chunk", {"chunk": chunk, "done": is_done}, room=sid)
                if is_done:
                    break
            if full_response:
                vc.add_to_conversation("assistant", full_response)
                vc.last_ai_response = full_response
                audio = vc.synthesize(full_response)
                audio_b64 = base64.b64encode(audio).decode("utf-8") if audio else None
                emit("response", {
                    "user_text": text,
                    "text": full_response,
                    "audio": audio_b64,
                    "streamed": True,
                }, room=sid)
        else:
            result = vc.process_text_message(text)
            if result.get("text"):
                audio_b64 = None
                if result.get("audio"):
                    audio_b64 = base64.b64encode(result["audio"]).decode("utf-8")
                emit("response", {
                    "user_text": result.get("user_text", ""),
                    "text": result["text"],
                    "audio": audio_b64,
                }, room=sid)
        _send_conversation(sid)
        _send_status(sid)
    except Exception as e:
        logger.error(f"Process text error: {e}")
        emit("error", {"message": str(e)}, room=sid)


@socketio.on("command")
def on_command(data):
    sid = request.sid
    session = get_or_create_session(sid)
    if not session:
        return
    vc = session["voice_chat"]
    username = session["username"]
    cmd = data.get("command")

    if cmd in ("pause",):
        setattr(vc, "paused", True)
    elif cmd in ("resume",):
        setattr(vc, "paused", False)
    elif cmd in ("clear", "new"):
        vc.clear_conversation_history()
        _send_conversation(sid)
    elif cmd == "save":
        vc.save_conversation()
        emit("notify", {"message": "Conversation saved", "type": "success"}, room=sid)
    elif cmd == "language":
        lang = data.get("language")
        if lang and vc.switch_language(lang):
            _save_config_field("language", lang)
            vc._save_user_settings()
            _send_config()

    elif cmd == "set_api_url":
        val = data.get("value", "")
        vc.config.api_url = val
        _save_config_field("api_url", val)

    elif cmd == "set_api_key":
        val = data.get("value", "")
        vc.config.api_key = val
        _save_config_field("api_key", val)

    elif cmd == "set_stt_backend":
        val = data.get("value", "whisper")
        vc.config.stt_backend = val
        _save_config_field("stt_backend", val)
        _send_config()
        emit("notify", {"message": "STT backend saved. Restart required.", "type": "warning"}, room=sid)

    elif cmd == "set_whisper_model":
        val = data.get("value", "turbo")
        vc.config.whisper_model = val
        _save_config_field("whisper_model", val)
        _send_config()
        emit("notify", {"message": "Whisper model saved. Restart required.", "type": "warning"}, room=sid)

    elif cmd == "set_tts_voice":
        lang = data.get("lang")
        model_path = data.get("model_path", "")
        config_path = data.get("config_path", "")
        if lang and lang in vc.config.languages:
            vc.config.languages[lang]["model_path"] = model_path
            vc.config.languages[lang]["config_path"] = config_path
            try:
                if os.path.exists("config.json"):
                    with open("config.json", "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    if lang in cfg_data.get("languages", {}):
                        cfg_data["languages"][lang]["model_path"] = model_path
                        cfg_data["languages"][lang]["config_path"] = config_path
                        with open("config.json", "w", encoding="utf-8") as f:
                            json.dump(cfg_data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save TTS config: {e}")
            _send_config()
            emit("notify", {"message": "TTS voice saved. Restart required.", "type": "warning"}, room=sid)

    elif cmd == "download_models":
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_model.py")
        if os.path.exists(script):
            try:
                subprocess.Popen(["python", script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            except AttributeError:
                subprocess.Popen(["python", script])
            emit("notify", {"message": "Model downloader opened.", "type": "info"}, room=sid)
        else:
            emit("notify", {"message": "download_model.py not found!", "type": "error"}, room=sid)

    elif cmd == "volume":
        val = max(0.1, min(2.0, float(data.get("value", 1.0))))
        vc.current_volume = val
        vc.synth_config.volume = val
        vc._save_user_settings()

    elif cmd == "speed":
        val = max(0.5, min(2.0, float(data.get("value", 1.0))))
        vc.current_speed = val
        vc.synth_config.length_scale = val
        vc._save_user_settings()

    elif cmd == "set_system_prompt":
        val = data.get("value", "")
        vc.config.custom_system_prompt = val
        _save_config_field("custom_system_prompt", val)
        emit("notify", {"message": "System prompt updated", "type": "success"}, room=sid)

    elif cmd == "set_api_model":
        val = data.get("value", "local-model")
        vc.config.api_model = val

    elif cmd == "retry":
        response = vc.retry_last_user_message()
        if response:
            audio = vc.synthesize(response)
            audio_b64 = base64.b64encode(audio).decode("utf-8") if audio else None
            emit("response", {
                "user_text": "",
                "text": response,
                "audio": audio_b64,
            }, room=sid)
            _send_conversation(sid)
            _send_status(sid)
        else:
            emit("notify", {"message": "No message to retry", "type": "warning"}, room=sid)

    elif cmd == "delete_message":
        index = data.get("index", -1)
        if vc.remove_message(index):
            _send_conversation(sid)

    elif cmd == "new_conversation":
        vc.save_conversation()
        vc.clear_conversation_history()
        vc.conversation_id = str(uuid.uuid4())[:8]
        _send_conversation(sid)
        _send_status(sid)
        _send_config(sid)

    elif cmd == "list_conversations":
        user_dir = get_user_dir(username)
        conv_dir = os.path.join(user_dir, "CONVERSATIONS")
        convs = []
        if os.path.exists(conv_dir):
            for fname in os.listdir(conv_dir):
                if fname.endswith(".json"):
                    convs.append(fname.replace(".json", ""))
        emit("conversations", {"list": convs}, room=sid)

    elif cmd == "load_conversation":
        cid = data.get("id", "default")
        user_dir = get_user_dir(username)
        path = os.path.join(user_dir, "CONVERSATIONS", f"{cid}.json")
        if vc.load_conversation(path):
            vc.conversation_id = cid
            _send_conversation(sid)
            _send_status(sid)
            _send_config(sid)
        else:
            emit("notify", {"message": f"Conversation '{cid}' not found", "type": "error"}, room=sid)

    elif cmd == "speak":
        text = data.get("text", "")
        if text:
            audio = vc.synthesize(text)
            audio_b64 = base64.b64encode(audio).decode("utf-8") if audio else None
            if audio_b64:
                emit("speak_audio", {"audio": audio_b64}, room=sid)
            else:
                emit("notify", {"message": "TTS not available for this text", "type": "error"}, room=sid)

    _send_status(sid)


@socketio.on("memory")
def on_memory(data):
    sid = request.sid
    session = get_or_create_session(sid)
    if not session:
        return
    username = session["username"]
    mm = MemoryManager(username)
    action = data.get("action")

    if action == "list":
        memory = mm.load_memory("memory")
        user = mm.load_memory("user")
        emit("memory_list", {
            "memory": memory,
            "user": user,
            "memory_usage": mm.get_usage("memory"),
            "user_usage": mm.get_usage("user"),
        }, room=sid)

    elif action == "add":
        target = data.get("target", "memory")
        content = data.get("content", "")
        if content and target != "soul":
            success, msg = mm.add_entry(target, content)
            emit("notify", {"message": msg, "type": "success" if success else "error"}, room=sid)

    elif action == "replace":
        target = data.get("target", "memory")
        old_text = data.get("old_text", "")
        content = data.get("content", "")
        if old_text and content and target != "soul":
            success, msg = mm.replace_entry(target, old_text, content)
            emit("notify", {"message": msg, "type": "success" if success else "error"}, room=sid)

    elif action == "remove":
        target = data.get("target", "memory")
        old_text = data.get("old_text", "")
        if old_text and target != "soul":
            success, msg = mm.remove_entry(target, old_text)
            emit("notify", {"message": msg, "type": "success" if success else "error"}, room=sid)

    elif action == "get_raw":
        target = data.get("target", "memory")
        content = mm.get_raw(target)
        emit("memory_raw", {"target": target, "content": content}, room=sid)

    elif action == "set_raw":
        target = data.get("target", "memory")
        content = data.get("content", "")
        mm.set_raw(target, content)
        emit("notify", {"message": f"{target.upper()} saved", "type": "success"}, room=sid)


def _send_conversation(sid):
    session = get_or_create_session(sid)
    if not session:
        return
    emit("conversation", {"messages": session["voice_chat"].get_conversation_history()}, room=sid)


def _send_status(sid):
    session = get_or_create_session(sid)
    if not session:
        return
    vc = session["voice_chat"]
    status = {
        "language": vc.current_language,
        "volume": vc.current_volume,
        "speed": vc.current_speed,
        "paused": getattr(vc, "paused", False),
        "mode": "idle",
        "stats": vc.get_stats(),
        "username": session["username"],
    }
    emit("status", status, room=sid)


def _send_config(sid=None):
    config = VoiceChatConfig()
    cfg = config.to_dict()
    if sid:
        session = get_or_create_session(sid)
        if session:
            vc = session["voice_chat"]
            cfg["username"] = session["username"]
            cfg["session_id"] = vc.conversation_id
            cfg["volume"] = vc.current_volume
            cfg["speed"] = vc.current_speed
            cfg["language"] = vc.current_language
        emit("config", cfg, room=sid)
    else:
        emit("config", cfg)


def _save_config_field(key, value):
    try:
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data[key] = value
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
    return False


if __name__ == "__main__":
    print("AI Voice Chat - Web Interface")
    print("Opening http://localhost:5000")
    import webbrowser
    webbrowser.open("http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
