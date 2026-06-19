import json
import os
import hashlib
import uuid
import time
import shutil

USERS_FILE = "memories/users.json"
USERS_DIR = "memories/users"

_sessions = {}


def _load_users() -> dict:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def _save_users(users: dict):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = os.urandom(32).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def _check_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split("$", 1)
        return _hash_password(password, salt) == stored
    except (ValueError, Exception):
        return False


def create_user(username: str, password: str):
    if len(username) < 2:
        return False, "Username must be at least 2 characters"
    if len(password) < 4:
        return False, "Password must be at least 4 characters"
    users = _load_users()
    if username in users:
        return False, "Username already exists"
    users[username] = {
        "password": _hash_password(password),
        "created": time.time(),
    }
    _save_users(users)
    _ensure_user_dirs(username)
    return True, "User created"


def verify_user(username: str, password: str) -> bool:
    users = _load_users()
    if username not in users:
        return False
    return _check_password(password, users[username]["password"])


def create_session(username: str) -> str:
    _clean_expired_sessions()
    token = str(uuid.uuid4())
    _sessions[token] = {"username": username, "created": time.time()}
    return token


def validate_session(token: str):
    _clean_expired_sessions()
    if token in _sessions:
        return _sessions[token]["username"]
    return None


def delete_session(token: str):
    _sessions.pop(token, None)


def delete_user_sessions(username: str):
    to_delete = [t for t, s in _sessions.items() if s["username"] == username]
    for t in to_delete:
        del _sessions[t]


def _clean_expired_sessions():
    now = time.time()
    expired = [t for t, s in list(_sessions.items()) if now - s["created"] > 86400]
    for t in expired:
        del _sessions[t]


def get_user_dir(username: str) -> str:
    return os.path.join(USERS_DIR, username)


def _ensure_user_dirs(username: str):
    user_dir = get_user_dir(username)
    conv_dir = os.path.join(user_dir, "CONVERSATIONS")
    os.makedirs(conv_dir, exist_ok=True)
    defaults = {
        "MEMORY.md": "# Memory\n\nKnowledge about projects, environment, and facts.\n",
        "USER.md": "# User Profile\n\nPreferences and personal information.\n",
        "SOUL.md": "# Personality\n\nYou are a helpful voice assistant.\n- Keep responses concise and natural.\n- Never use markdown formatting in responses.\n- Match the user's language.\n",
        "user_settings.json": '{"volume": 1.1, "speed": 1.05, "language": "en"}\n',
    }
    for name, content in defaults.items():
        path = os.path.join(user_dir, name)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


def delete_user(username: str):
    users = _load_users()
    users.pop(username, None)
    _save_users(users)
    delete_user_sessions(username)
    user_dir = get_user_dir(username)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)


def list_users() -> list:
    return list(_load_users().keys())
