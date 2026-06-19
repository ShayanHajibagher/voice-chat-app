import vosk
import requests
import tempfile
import os
import wave
import logging
import json
import io
import time
import re
from typing import Optional
from piper import PiperVoice
from piper.config import SynthesisConfig

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VoiceChatConfig:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        defaults = {
            "language": "en",
            "stt_backend": "whisper",
            "whisper_model": "turbo",
            "languages": {
                "en": {
                    "vosk_model_path": "vosk-model-small-en-us-0.15",
                    "model_path": "en_US-lessac-high.onnx",
                    "config_path": "en_US-lessac-high.onnx.json",
                },
                "fa": {
                    "vosk_model_path": "vosk-model-small-fa-rhasspy-0.15",
                    "model_path": "fa_IR-mana-medium.onnx",
                    "config_path": "fa_IR-mana-medium.onnx.json",
                },
            },
            "api_url": "http://localhost:1234/v1/chat/completions",
            "api_key": "",
            "api_timeout": 60,
            "max_retries": 3,
            "sample_rate": 16000,
            "chunk_size": 8192,
            "max_tokens": 1500,
            "temperature": 0.7,
            "silence_threshold": 1.0,
            "silence_duration": 1.0,
            "synth": {
                "volume": 1.1,
                "length_scale": 1.05,
                "noise_scale": 0.4,
                "noise_w_scale": 0.5,
                "normalize_audio": True,
            },
            "custom_system_prompt": "",
        }

        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                user_config = json.load(f)
                self._deep_update(defaults, user_config)

        for key, value in defaults.items():
            setattr(self, key, value)

        self._set_language_models()
        logger.info(f"Configuration loaded from {self.config_file}")

    def _set_language_models(self):
        lang_config = self.languages.get(self.language, self.languages["en"])
        self.vosk_model_path = lang_config["vosk_model_path"]
        self.model_path = lang_config["model_path"]
        self.config_path = lang_config["config_path"]
        logger.info(f"Language set to: {self.language}")

    def set_language(self, language: str):
        if language in self.languages:
            self.language = language
            self._set_language_models()
            return True
        logger.warning(
            f"Language '{language}' not available. Available: {list(self.languages.keys())}"
        )
        return False

    def _deep_update(self, base: dict, update: dict):
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def to_dict(self):
        return {
            "language": self.language,
            "stt_backend": self.stt_backend,
            "whisper_model": self.whisper_model,
            "api_url": self.api_url,
            "api_key": self.api_key,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "custom_system_prompt": self.custom_system_prompt,
            "languages": self.languages,
            "synth": {
                "volume": self.synth.get("volume", 1.0),
                "length_scale": self.synth.get("length_scale", 1.0),
            },
        }


class VoiceChat:
    def __init__(self, config: VoiceChatConfig, conversation_options: Optional[dict] = None, username: str = "default"):
        self.config = config
        self.username = username
        self.conversation_options = conversation_options or {}
        self.stt_backend = config.stt_backend
        self.whisper_model_name = config.whisper_model
        self.current_language = config.language
        self.conversation_id = None

        self.whisper_model = None
        self.vosk_model = None

        if self.stt_backend == "whisper":
            self._load_whisper_model()
        else:
            self.vosk_model = self._load_vosk_model()

        self.voice = self._load_tts_model()
        self.synth_config = self._create_synth_config()
        self.conversation_history = []
        self.current_volume = config.synth.get("volume", 1.0)
        self.current_speed = config.synth.get("length_scale", 1.0)

        self.conversation_stats = {
            "user_messages": 0,
            "ai_messages": 0,
            "words_spoken": 0,
            "start_time": time.time(),
        }

        from auth_manager import get_user_dir
        self.settings_file = os.path.join(get_user_dir(self.username), "user_settings.json")
        self._load_user_settings()
        self._last_ai_response = ""
        logger.info("VoiceChat initialized successfully")

    def _load_whisper_model(self):
        try:
            from faster_whisper import WhisperModel
            model_name = self.whisper_model_name or "turbo"
            logger.info(f"Loading Whisper model: {model_name}")
            self.whisper_model = WhisperModel(
                model_name, device="cpu", compute_type="int8"
            )
            logger.info(f"Whisper model loaded: {model_name}")
        except ImportError:
            logger.warning("faster-whisper not installed, falling back to Vosk")
            self.stt_backend = "vosk"
            self.vosk_model = self._load_vosk_model()
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.stt_backend = "vosk"
            self.vosk_model = self._load_vosk_model()

    def _load_vosk_model(self):
        if not os.path.exists(self.config.vosk_model_path):
            logger.warning(f"Vosk model not found: {self.config.vosk_model_path}")
            return None
        try:
            vosk.SetLogLevel(0)
            model = vosk.Model(self.config.vosk_model_path)
            logger.info(f"Vosk model loaded: {self.config.vosk_model_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            return None

    def _load_tts_model(self):
        if not os.path.exists(self.config.model_path):
            logger.warning(f"TTS model not found: {self.config.model_path}")
            return None
        try:
            voice = PiperVoice.load(self.config.model_path, self.config.config_path)
            logger.info(f"TTS model loaded: {self.config.model_path}")
            return voice
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            return None

    def _create_synth_config(self) -> SynthesisConfig:
        return SynthesisConfig(
            volume=self.config.synth["volume"],
            length_scale=self.config.synth["length_scale"],
            noise_scale=self.config.synth["noise_scale"],
            noise_w_scale=self.config.synth["noise_w_scale"],
            normalize_audio=self.config.synth["normalize_audio"],
        )

    def _save_user_settings(self):
        try:
            settings = {"volume": self.current_volume, "speed": self.current_speed, "language": self.current_language}
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save user settings: {e}")

    def _load_user_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                if "volume" in settings:
                    self.current_volume = settings["volume"]
                    self.synth_config.volume = self.current_volume
                if "speed" in settings:
                    self.current_speed = settings["speed"]
                    self.synth_config.length_scale = self.current_speed
                if "language" in settings:
                    self.current_language = settings["language"]
                logger.info("User settings loaded")
        except Exception as e:
            logger.warning(f"Could not load user settings: {e}")

    def add_to_conversation(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content, "timestamp": time.time()})
        self._update_stats(role, content)

    def get_conversation_history(self) -> list:
        return self.conversation_history

    def clear_conversation_history(self):
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def remove_message(self, index: int) -> bool:
        if 0 <= index < len(self.conversation_history):
            removed = self.conversation_history.pop(index)
            logger.info(f"Removed message at index {index}: role={removed['role']}")
            return True
        return False

    def save_conversation(self, filename: str = None):
        if not filename:
            from auth_manager import get_user_dir
            base = get_user_dir(self.username)
            filename = os.path.join(base, "CONVERSATIONS", f"{self.conversation_id or 'default'}.json")
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            from crypto_manager import encrypt_blob
            data = json.dumps(self.conversation_history, indent=2, ensure_ascii=False).encode("utf-8")
            encrypted = encrypt_blob(data)
            with open(filename, "wb") as f:
                f.write(encrypted)
            logger.info(f"Conversation saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

    def load_conversation(self, filename: str) -> bool:
        try:
            with open(filename, "rb") as f:
                raw = f.read()
            if raw.startswith(b"gAAAAA"):
                from crypto_manager import decrypt_blob
                raw = decrypt_blob(raw)
            self.conversation_history = json.loads(raw.decode("utf-8"))
            return True
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return False

    def _update_stats(self, role: str, content: str):
        if role == "user":
            self.conversation_stats["user_messages"] += 1
            self.conversation_stats["words_spoken"] += len(content.split())
        elif role == "assistant":
            self.conversation_stats["ai_messages"] += 1

    def get_stats(self) -> dict:
        elapsed = int(time.time() - self.conversation_stats["start_time"])
        return {
            "user_messages": self.conversation_stats["user_messages"],
            "ai_messages": self.conversation_stats["ai_messages"],
            "words_spoken": self.conversation_stats["words_spoken"],
            "elapsed": elapsed,
            "language": self.current_language,
            "volume": self.current_volume,
            "speed": self.current_speed,
        }

    def get_available_languages(self) -> list:
        return list(self.config.languages.keys())

    def transcribe(self, audio_bytes: bytes) -> str:
        if self.stt_backend == "whisper":
            return self._transcribe_whisper(audio_bytes)
        else:
            return self._transcribe_vosk(audio_bytes)

    def _transcribe_whisper(self, audio_bytes: bytes) -> str:
        import numpy as np
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
                rate = wav.getframerate()
                frames = wav.readframes(wav.getnframes())
            audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self.whisper_model.transcribe(
                audio_np, language=self.current_language,
                beam_size=5, vad_filter=True,
            )
            return " ".join(s.text for s in segments).strip()
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""

    def _transcribe_vosk(self, audio_bytes: bytes) -> str:
        if self.vosk_model is None:
            logger.error("Vosk model not loaded, cannot transcribe")
            return ""
        try:
            recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
                return result.get("text", "").strip()
            partial = json.loads(recognizer.PartialResult())
            return partial.get("partial", "").strip()
        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            return ""

    def clean_text_for_tts(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"\*\*\*(.*?)\*\*\*", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"\*(\w+)\*", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"___(.*?)___", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"__(.*?)__", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"_(.*?)_", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"`(.*?)`", r"\1", text)
        text = re.sub(r"^(#+)\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
        text = re.sub(r"^[\-\*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*+", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def synthesize(self, text: str) -> Optional[bytes]:
        if self.voice is None:
            logger.warning("TTS voice not loaded, skipping synthesis")
            return None
        cleaned = self.clean_text_for_tts(text)
        logger.info(f"TTS synthesize: {cleaned[:80]}...")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_file = f.name
        try:
            with wave.open(wav_file, "wb") as wav:
                self.voice.synthesize_wav(cleaned, wav, syn_config=self.synth_config)
            with open(wav_file, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return None
        finally:
            if os.path.exists(wav_file):
                os.unlink(wav_file)

    def process_audio_message(self, audio_bytes: bytes) -> dict:
        text = self.transcribe(audio_bytes)
        if not text:
            return {"text": "", "user_text": "", "audio": None}
        self.add_to_conversation("user", text)
        response = self.chat_with_ai(text)
        if response:
            self.add_to_conversation("assistant", response)
            audio = self.synthesize(response)
            return {"text": response, "user_text": text, "audio": audio, "full_response": response}
        return {"text": "", "user_text": text, "audio": None}

    def process_text_message(self, text: str) -> dict:
        if not text or not text.strip():
            return {"text": "", "audio": None}
        text = text.strip()
        self.add_to_conversation("user", text)
        response = self.chat_with_ai(text)
        if response:
            self.add_to_conversation("assistant", response)
            audio = self.synthesize(response)
            return {"text": response, "user_text": text, "audio": audio, "full_response": response}
        return {"text": "", "user_text": text, "audio": None}

    def chat_with_ai_stream(self, user_input: str):
        messages = self._build_messages(user_input)
        payload = {
            "messages": messages,
            "model": "local-model",
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }
        headers = {"Content-Type": "application/json"}
        api_key = getattr(self.config, "api_key", "") or ""
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    self.config.api_url, json=payload, headers=headers, timeout=self.config.api_timeout, stream=True
                )
                if response.status_code == 200:
                    full_content = ""
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode("utf-8").strip()
                            if decoded.startswith("data: "):
                                data_str = decoded[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_content += content
                                        yield content, False
                                except json.JSONDecodeError:
                                    continue
                    yield full_content, True
                    return
                logger.warning(f"API {response.status_code}, attempt {attempt + 1}/{self.config.max_retries}")
            except requests.RequestException as e:
                logger.warning(f"Request error ({attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    yield f"Error connecting to AI after {self.config.max_retries} attempts.", True
                    return

    def _build_messages(self, user_input: str):
        memory_block = self._get_memory_block()
        soul_block = self._get_soul_block()
        system_prompt_content = (
            f"You are a helpful voice assistant. "
            f"Current language: {self.current_language.upper()}. "
            f"Respond in the same language as the user ({'English' if self.current_language == 'en' else 'Persian/Farsi'}). "
            f"Keep responses concise, natural, and suitable for speech output. "
            f"Avoid markdown formatting, bullet points, or code blocks. "
            f"Current date: {time.strftime('%Y-%m-%d')}."
        )
        if soul_block:
            system_prompt_content += f"\n\n{soul_block}"
        if memory_block:
            system_prompt_content += f"\n\n{memory_block}"
        custom = getattr(self.config, "custom_system_prompt", "")
        if custom:
            system_prompt_content += f"\n\nAdditional instructions: {custom}"
        system_prompt = {"role": "system", "content": system_prompt_content}
        return [system_prompt] + self.conversation_history + [{"role": "user", "content": user_input}]

    def _get_soul_block(self) -> str:
        try:
            from memory_manager import MemoryManager
            mm = MemoryManager(self.username)
            soul = mm.load_soul()
            if soul:
                return f"═" * 60 + f"\nPERSONALITY\n" + f"═" * 60 + f"\n{soul}"
            return ""
        except ImportError:
            return ""
        except Exception as e:
            logger.warning(f"Failed to load SOUL.md: {e}")
            return ""

    def _get_memory_block(self) -> str:
        try:
            from memory_manager import MemoryManager
            mm = MemoryManager(self.username)
            return mm.format_memory_block()
        except ImportError:
            return ""
        except Exception as e:
            logger.warning(f"Failed to load memory: {e}")
            return ""

    def chat_with_ai(self, user_input: str) -> Optional[str]:
        messages = self._build_messages(user_input)
        payload = {
            "messages": messages,
            "model": "local-model",
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        headers = {"Content-Type": "application/json"}
        api_key = getattr(self.config, "api_key", "") or ""
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    self.config.api_url, json=payload, headers=headers, timeout=self.config.api_timeout
                )
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    self._process_memory_actions(content)
                    return content
                logger.warning(f"API {response.status_code}, attempt {attempt + 1}/{self.config.max_retries}")
            except requests.RequestException as e:
                logger.warning(f"Request error ({attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    return f"Error connecting to AI after {self.config.max_retries} attempts."
        return "Sorry, I couldn't get a response from the AI."

    def _process_memory_actions(self, response: str):
        try:
            import re
            pattern = r'\{[^}]*"memory_action"[^}]*\}'
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    action = json.loads(match)
                    from memory_manager import MemoryManager
                    mm = MemoryManager(self.username)
                    act = action.get("memory_action")
                    target = action.get("target", "memory")
                    content = action.get("content", "")
                    old_text = action.get("old_text", "")
                    if act == "add":
                        mm.add_entry(target, content)
                    elif act == "replace" and old_text:
                        mm.replace_entry(target, old_text, content)
                    elif act == "remove" and old_text:
                        mm.remove_entry(target, old_text)
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Memory action parse error: {e}")
        except Exception as e:
            logger.warning(f"Memory processing error: {e}")

    def switch_language(self, language: str) -> bool:
        if self.config.set_language(language):
            self.current_language = language
            if self.stt_backend == "vosk":
                self.vosk_model = self._load_vosk_model()
            self.voice = self._load_tts_model()
            self.synth_config = self._create_synth_config()
            return True
        return False

    def get_conversation_json(self):
        return json.dumps(self.conversation_history, indent=2, ensure_ascii=False)

    def get_conversation_text(self):
        lines = []
        for msg in self.conversation_history:
            role = "You" if msg["role"] == "user" else "AI"
            lines.append(f"[{role}]")
            lines.append(msg["content"])
            lines.append("")
        return "\n".join(lines)

    def get_conversation_markdown(self):
        lines = []
        for msg in self.conversation_history:
            role = "**You**" if msg["role"] == "user" else "**AI Assistant**"
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(msg.get("timestamp", 0)))
            lines.append(f"### {role} _{ts}_")
            lines.append("")
            lines.append(msg["content"])
            lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    @property
    def last_ai_response(self) -> str:
        return self._last_ai_response

    @last_ai_response.setter
    def last_ai_response(self, value: str):
        self._last_ai_response = value

    def retry_last_user_message(self) -> Optional[str]:
        user_msgs = [m for m in self.conversation_history if m["role"] == "user"]
        if not user_msgs:
            return None
        last_user = user_msgs[-1]["content"]
        ai_msgs = [m for m in self.conversation_history if m["role"] == "assistant"]
        if ai_msgs:
            last_ai = ai_msgs[-1]
            self.conversation_history.remove(last_ai)
        response = self.chat_with_ai(last_user)
        if response:
            self.add_to_conversation("assistant", response)
            return response
        return None
