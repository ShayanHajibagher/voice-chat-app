import os
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

KEY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memories")
KEY_FILE = os.path.join(KEY_DIR, ".crypto_key")


def _get_or_create_key() -> bytes:
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read().strip()
    key = Fernet.generate_key()
    os.makedirs(KEY_DIR, exist_ok=True)
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    logger.info("Encryption key created at %s", KEY_FILE)
    return key


def encrypt_blob(data: bytes) -> bytes:
    f = Fernet(_get_or_create_key())
    return f.encrypt(data)


def decrypt_blob(data: bytes) -> bytes:
    f = Fernet(_get_or_create_key())
    return f.decrypt(data)


def encrypt_file(filepath: str):
    if not os.path.exists(filepath):
        return
    with open(filepath, "rb") as f:
        plaintext = f.read()
    ciphertext = encrypt_blob(plaintext)
    with open(filepath, "wb") as f:
        f.write(ciphertext)


def decrypt_file(filepath: str) -> bytes:
    if not os.path.exists(filepath):
        return b""
    with open(filepath, "rb") as f:
        ciphertext = f.read()
    try:
        return decrypt_blob(ciphertext)
    except Exception:
        return b""
