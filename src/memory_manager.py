import os
import logging
from auth_manager import get_user_dir

logger = logging.getLogger(__name__)

MEMORY_CHAR_LIMIT = 2200
USER_CHAR_LIMIT = 1375

SEPARATOR = "§"
MEMORY_FILE_NAME = "MEMORY.md"
USER_FILE_NAME = "USER.md"
SOUL_FILE_NAME = "SOUL.md"


class MemoryManager:
    def __init__(self, username: str = "default"):
        self.username = username
        self.base_dir = get_user_dir(username)
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, filename: str) -> str:
        return os.path.join(self.base_dir, filename)

    def _read_entries(self, path: str) -> list:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        return [e.strip() for e in content.split(SEPARATOR) if e.strip()]

    def _write_entries(self, path: str, entries: list):
        with open(path, "w", encoding="utf-8") as f:
            f.write((f" {SEPARATOR} ".join(entries)).strip())

    def load_memory(self, target: str = "memory") -> list:
        if target == "soul":
            return []
        name = MEMORY_FILE_NAME if target == "memory" else USER_FILE_NAME
        return self._read_entries(self._path(name))

    def get_raw(self, target: str = "memory") -> str:
        name = SOUL_FILE_NAME if target == "soul" else (MEMORY_FILE_NAME if target == "memory" else USER_FILE_NAME)
        path = self._path(name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def set_raw(self, target: str, content: str):
        name = SOUL_FILE_NAME if target == "soul" else (MEMORY_FILE_NAME if target == "memory" else USER_FILE_NAME)
        with open(self._path(name), "w", encoding="utf-8") as f:
            f.write(content)

    def get_limit(self, target: str) -> int:
        if target == "soul":
            return 10000
        return MEMORY_CHAR_LIMIT if target == "memory" else USER_CHAR_LIMIT

    def get_usage(self, target: str) -> dict:
        name = SOUL_FILE_NAME if target == "soul" else (MEMORY_FILE_NAME if target == "memory" else USER_FILE_NAME)
        path = self._path(name)
        limit = self.get_limit(target)
        current = 0
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                current = len(f.read())
        return {"current": current, "limit": limit, "percent": round((current / limit) * 100, 1) if limit > 0 else 0}

    def add_entry(self, target: str, content: str):
        if target == "soul":
            return False, "Cannot add entries to SOUL.md. Edit raw content instead."
        name = MEMORY_FILE_NAME if target == "memory" else USER_FILE_NAME
        path = self._path(name)
        limit = self.get_limit(target)
        entries = self._read_entries(path)
        if content in entries:
            return True, "Entry already exists (duplicate skipped)"
        new_raw = (f" {SEPARATOR} ".join(entries + [content])).strip() if entries else content
        if len(new_raw) > limit:
            usage = self.get_usage(target)
            return False, f"Memory at {usage['current']}/{usage['limit']} chars. Free space first."
        self._write_entries(path, entries + [content])
        logger.info(f"Memory entry added to {target}: {content[:60]}...")
        return True, "Entry added"

    def replace_entry(self, target: str, old_text: str, new_content: str):
        if target == "soul":
            return False, "Cannot replace entries in SOUL.md."
        name = MEMORY_FILE_NAME if target == "memory" else USER_FILE_NAME
        path = self._path(name)
        limit = self.get_limit(target)
        entries = self._read_entries(path)
        matching = [i for i, e in enumerate(entries) if old_text in e]
        if not matching:
            return False, f"No entry containing '{old_text}' found"
        if len(matching) > 1:
            return False, f"'{old_text}' matches multiple entries."
        idx = matching[0]
        entries[idx] = new_content
        new_raw = (f" {SEPARATOR} ".join(entries)).strip()
        if len(new_raw) > limit:
            return False, f"Replacement would exceed {limit} char limit."
        self._write_entries(path, entries)
        return True, "Entry replaced"

    def remove_entry(self, target: str, old_text: str):
        if target == "soul":
            return False, "Cannot remove entries from SOUL.md."
        name = MEMORY_FILE_NAME if target == "memory" else USER_FILE_NAME
        path = self._path(name)
        entries = self._read_entries(path)
        matching = [i for i, e in enumerate(entries) if old_text in e]
        if not matching:
            return False, f"No entry containing '{old_text}' found"
        if len(matching) > 1:
            return False, f"'{old_text}' matches multiple entries."
        entries.pop(matching[0])
        self._write_entries(path, entries)
        return True, "Entry removed"

    def format_memory_block(self) -> str:
        memory_entries = self.load_memory("memory")
        user_entries = self.load_memory("user")
        m_usage = self.get_usage("memory")
        u_usage = self.get_usage("user")
        lines = []
        if memory_entries:
            lines.append("═" * 60)
            lines.append(f"MEMORY [{m_usage['percent']}% — {m_usage['current']}/{m_usage['limit']} chars]")
            lines.append("═" * 60)
            for i, entry in enumerate(memory_entries):
                lines.append(entry)
                if i < len(memory_entries) - 1:
                    lines.append(SEPARATOR)
        if user_entries:
            if lines:
                lines.append("")
            lines.append("═" * 60)
            lines.append(f"USER PROFILE [{u_usage['percent']}% — {u_usage['current']}/{u_usage['limit']} chars]")
            lines.append("═" * 60)
            for i, entry in enumerate(user_entries):
                lines.append(entry)
                if i < len(user_entries) - 1:
                    lines.append(SEPARATOR)
        return "\n".join(lines)

    def load_soul(self) -> str:
        path = self._path(SOUL_FILE_NAME)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""
