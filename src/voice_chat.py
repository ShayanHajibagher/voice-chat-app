import vosk
import requests
import winsound
import tempfile
import os
import wave
import logging
import json
import pyaudio
import keyboard
import threading
import time
import io
import struct
from typing import Optional
from piper import PiperVoice
from piper.config import SynthesisConfig
from animations import *
from window_focus import *

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Color:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"


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
            "max_tokens": 150,
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


class VoiceChat:
    def __init__(self, config: VoiceChatConfig, conversation_options: Optional[dict] = None):
        self.config = config
        self.conversation_options = conversation_options or {}
        self.stt_backend = config.stt_backend
        self.whisper_model_name = config.whisper_model
        self.current_language = config.language

        self.whisper_model = None
        self.vosk_model = None

        if self.stt_backend == "whisper":
            self._load_whisper_model()
        else:
            self.vosk_model = self._load_vosk_model()

        self.voice = self._load_tts_model()
        self.synth_config = self._create_synth_config()
        self.conversation_history = []
        self.audio = pyaudio.PyAudio()
        self.paused = False
        self.keyboard_command = None
        self.current_volume = config.synth.get("volume", 1.0)
        self.current_speed = config.synth.get("length_scale", 1.0)
        self.status_display = status_display()
        self._paused_message_shown = False
        self.conversation_file = "conversation.json"
        self._setup_keyboard_listener()
        self._auto_load_conversation()
        self._setup_window_monitoring()

        self.conversation_stats = {
            "user_messages": 0,
            "ai_messages": 0,
            "words_spoken": 0,
            "start_time": time.time(),
        }

        self.settings_file = "user_settings.json"
        self._load_user_settings()
        logger.info("VoiceChat initialized successfully")

    def _load_whisper_model(self):
        try:
            from faster_whisper import WhisperModel
            model_name = self.whisper_model_name or "turbo"
            logger.info(f"Loading Whisper model: {model_name}")
            print(f"{Colors.BRIGHT_YELLOW}Loading Whisper STT ({model_name})...{Colors.RESET}")
            self.whisper_model = WhisperModel(
                model_name, device="cpu", compute_type="int8"
            )
            logger.info(f"Whisper model loaded: {model_name}")
        except ImportError:
            logger.warning("faster-whisper not installed, falling back to Vosk")
            print(f"{Colors.BRIGHT_YELLOW}faster-whisper not found, using Vosk STT{Colors.RESET}")
            self.stt_backend = "vosk"
            self.vosk_model = self._load_vosk_model()
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            print(f"{Colors.BRIGHT_RED}Whisper load failed: {e}, falling back to Vosk{Colors.RESET}")
            self.stt_backend = "vosk"
            self.vosk_model = self._load_vosk_model()

    def _load_vosk_model(self) -> vosk.Model:
        try:
            vosk.SetLogLevel(0)
            model = vosk.Model(self.config.vosk_model_path)
            logger.info(f"Vosk model loaded: {self.config.vosk_model_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            raise

    def _load_tts_model(self) -> PiperVoice:
        try:
            voice = PiperVoice.load(self.config.model_path, self.config.config_path)
            logger.info(f"TTS model loaded: {self.config.model_path}")
            return voice
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise

    def _create_synth_config(self) -> SynthesisConfig:
        return SynthesisConfig(
            volume=self.config.synth["volume"],
            length_scale=self.config.synth["length_scale"],
            noise_scale=self.config.synth["noise_scale"],
            noise_w_scale=self.config.synth["noise_w_scale"],
            normalize_audio=self.config.synth["normalize_audio"],
        )

    # ---- Keyboard & Window ----

    def _setup_keyboard_listener(self):
        keyboard.add_hotkey("q", lambda: self._set_keyboard_command("quit"))
        keyboard.add_hotkey("esc", lambda: self._set_keyboard_command("quit"))
        keyboard.add_hotkey("p", lambda: self._set_keyboard_command("pause"))
        keyboard.add_hotkey("r", lambda: self._set_keyboard_command("resume"))
        keyboard.add_hotkey("e", lambda: self._set_keyboard_command("english"))
        keyboard.add_hotkey("f", lambda: self._set_keyboard_command("persian"))
        keyboard.add_hotkey("l", lambda: self._set_keyboard_command("languages"))
        keyboard.add_hotkey("s", lambda: self._set_keyboard_command("save"))
        keyboard.add_hotkey("n", lambda: self._set_keyboard_command("new"))
        keyboard.add_hotkey("t", lambda: self._set_keyboard_command("stats"))
        keyboard.add_hotkey("up", lambda: self._adjust_volume(0.1))
        keyboard.add_hotkey("down", lambda: self._adjust_volume(-0.1))
        keyboard.add_hotkey("right", lambda: self._adjust_speed(-0.05))
        keyboard.add_hotkey("left", lambda: self._adjust_speed(0.05))
        logger.info("Keyboard hotkeys registered")

    def _set_keyboard_command(self, command):
        if not is_window_active():
            self.status_display.show_status("INPUT_IGNORED", "Window minimized - input ignored", Colors.BRIGHT_YELLOW)
            return
        self.keyboard_command = command
        logger.info(f"Keyboard command received: {command}")

    def _setup_window_monitoring(self):
        self.window_monitor = start_window_monitoring()

        @on_window_minimized
        def on_minimized():
            self.status_display.show_status("WINDOW_MINIMIZED", "Window minimized - keyboard input disabled", Colors.BRIGHT_YELLOW)

        @on_window_restored
        def on_restored():
            self.status_display.show_status("WINDOW_RESTORED", "Window restored - keyboard input enabled", Colors.BRIGHT_GREEN)

    def _adjust_volume(self, delta):
        if not is_window_active():
            return
        self.current_volume = max(0.1, min(2.0, self.current_volume + delta))
        self.synth_config.volume = self.current_volume
        print(f"\n{Colors.CYAN}Volume: {self.current_volume:.1f}{Colors.RESET}")

    def _adjust_speed(self, delta):
        if not is_window_active():
            return
        self.current_speed = max(0.5, min(2.0, self.current_speed + delta))
        self.synth_config.length_scale = self.current_speed
        print(f"\n{Colors.CYAN}Speed: {self.current_speed:.2f}{Colors.RESET}")

    def _play_sound(self, sound_type: str):
        try:
            sounds = {
                "pause": (440, 200), "resume": (880, 200), "language": (660, 300),
                "save": (523, 150), "error": (200, 500), "success": (1047, 200),
            }
            if sound_type in sounds:
                freq, dur = sounds[sound_type]
                winsound.Beep(freq, dur)
        except Exception as e:
            logger.warning(f"Could not play sound: {e}")

    # ---- Settings Persistence ----

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

    # ---- Conversation Management ----

    def _auto_load_conversation(self):
        opts = getattr(self, "conversation_options", {}) or {}
        if opts.get("fresh"):
            print(f"{Colors.BRIGHT_YELLOW}Starting fresh conversation...{Colors.RESET}\n")
            self.conversation_history = []
            return
        if "load_file" in opts:
            if self.load_conversation(opts["load_file"]):
                return
            print(f"{Colors.BRIGHT_YELLOW}Could not load file, starting fresh...{Colors.RESET}\n")
            self.conversation_history = []
            return
        if os.path.exists(self.conversation_file):
            try:
                with open(self.conversation_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data:
                    print(f"\n{Colors.BRIGHT_YELLOW}Previous conversation found!{Colors.RESET}")
                    print(f"{Colors.BRIGHT_CYAN}Messages: {len(data)}{Colors.RESET}")
                    choice = input("Load previous conversation? (y/n): ").strip().lower()
                    if choice in ("y", "yes"):
                        self.conversation_history = data
                        print(f"{Colors.BRIGHT_GREEN}[OK] Loaded{Colors.RESET}\n")
                    else:
                        self.conversation_history = []
                else:
                    self.conversation_history = []
            except Exception as e:
                print(f"{Colors.BRIGHT_RED}Load error: {e}{Colors.RESET}")
                self.conversation_history = []
        else:
            self.conversation_history = []

    def add_to_conversation(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        self._update_stats(role, content)

    def get_conversation_history(self) -> list:
        return self.conversation_history

    def clear_conversation_history(self):
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def save_conversation(self, filename: str = None, silent: bool = False):
        if not filename:
            filename = self.conversation_file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            if not silent:
                print(f"\n{Color.GREEN}[OK] Saved to: {filename}{Color.RESET}\n")
                self._play_sound("save")
            logger.info(f"Conversation saved to {filename}")
        except Exception as e:
            if not silent:
                print(f"\n{Color.RED}[FAIL] Save failed: {e}{Color.RESET}\n")
                self._play_sound("error")
            logger.error(f"Failed to save conversation: {e}")

    def load_conversation(self, filename: str):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.conversation_history = json.load(f)
            print(f"\n{Color.GREEN}[OK] Loaded from: {filename}{Color.RESET}\n")
            return True
        except Exception as e:
            print(f"\n{Color.RED}[FAIL] Load failed: {e}{Color.RESET}\n")
            return False

    def _update_stats(self, role: str, content: str):
        if role == "user":
            self.conversation_stats["user_messages"] += 1
            self.conversation_stats["words_spoken"] += len(content.split())
        elif role == "assistant":
            self.conversation_stats["ai_messages"] += 1

    def _show_stats(self):
        elapsed = int(time.time() - self.conversation_stats["start_time"])
        stats = {
            "user_messages": self.conversation_stats["user_messages"],
            "ai_messages": self.conversation_stats["ai_messages"],
            "words_spoken": self.conversation_stats["words_spoken"],
            "elapsed_time": elapsed,
            "language": self.current_language,
            "volume": self.current_volume,
            "speed": self.current_speed,
        }
        ChatDisplay.show_conversation_stats(stats)

    def get_available_languages(self) -> list:
        return list(self.config.languages.keys())

    # ---- STT: Transcribe ----

    def transcribe(self, audio_bytes: bytes, language: str = None) -> str:
        if self.stt_backend == "whisper":
            return self._transcribe_whisper(audio_bytes, language)
        else:
            return self._transcribe_vosk(audio_bytes)

    def _transcribe_whisper(self, audio_bytes: bytes, language: str = None) -> str:
        import numpy as np
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
                rate = wav.getframerate()
                frames = wav.readframes(wav.getnframes())
            audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self.whisper_model.transcribe(
                audio_np, language=language or self.current_language,
                beam_size=5, vad_filter=True,
            )
            return " ".join(s.text for s in segments).strip()
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""

    def _transcribe_vosk(self, audio_bytes: bytes) -> str:
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

    # ---- TTS: Synthesize ----

    def clean_text_for_tts(self, text: str) -> str:
        import re
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

    # ---- Full Pipeline (Web mode) ----

    def process_audio_message(self, audio_bytes: bytes) -> dict:
        text = self.transcribe(audio_bytes)
        if not text:
            return {"text": "", "user_text": "", "audio": None}
        self.add_to_conversation("user", text)
        response = self.chat_with_ai(text)
        if response:
            self.add_to_conversation("assistant", response)
            audio = self.synthesize(response)
            return {"text": response, "user_text": text, "audio": audio}
        return {"text": "", "user_text": text, "audio": None}

    # ---- AI Backend ----

    def chat_with_ai(self, user_input: str) -> Optional[str]:
        system_prompt = {
            "role": "system",
            "content": (
                f"You are a helpful voice assistant. "
                f"Current language: {self.current_language.upper()}. "
                f"Respond in the same language as the user ({'English' if self.current_language == 'en' else 'Persian/Farsi'}). "
                f"Keep responses concise, natural, and suitable for speech output. "
                f"Avoid markdown formatting, bullet points, or code blocks. "
                f"Current date: {time.strftime('%Y-%m-%d')}."
            ),
        }
        messages = [system_prompt] + self.conversation_history + [{"role": "user", "content": user_input}]
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
                    return response.json()["choices"][0]["message"]["content"]
                logger.warning(f"API {response.status_code}, attempt {attempt + 1}/{self.config.max_retries}")
            except requests.RequestException as e:
                logger.warning(f"Request error ({attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    return f"Error connecting to AI after {self.config.max_retries} attempts."
        return "Sorry, I couldn't get a response from the AI."

    # ---- CLI Mode ----

    def switch_language(self, language: str) -> bool:
        if self.config.set_language(language):
            print(f"\n{Colors.BRIGHT_YELLOW}Switching to {language.upper()}...{Colors.RESET}")
            self.current_language = language
            if self.stt_backend == "vosk":
                self.vosk_model = self._load_vosk_model()
            self.voice = self._load_tts_model()
            self.synth_config = self._create_synth_config()
            print(f"\n{Color.GREEN}[OK] Switched to {language.upper()}{Color.RESET}\n")
            self._play_sound("language")
            return True
        return False

    def listen(self) -> Optional[str]:
        if self.stt_backend == "whisper":
            return self._listen_whisper()
        return self._listen_vosk()

    def _listen_whisper(self) -> Optional[str]:
        CHUNK = 16000
        stream = self.audio.open(
            format=pyaudio.paInt16, channels=1, rate=16000,
            input=True, frames_per_buffer=CHUNK,
        )
        try:
            logger.info("Listening (Whisper)...")
            frames = []
            silent_chunks = 0
            max_silent = int(self.config.silence_duration * 16000 / CHUNK)
            recording = False

            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                level = max(struct.unpack("<" + "h" * (len(data) // 2), data))
                if level > 500:
                    recording = True
                    silent_chunks = 0
                elif recording:
                    silent_chunks += 1
                    if silent_chunks >= max_silent:
                        break
                if self.keyboard_command:
                    stream.stop_stream(); stream.close()
                    return None

            stream.stop_stream(); stream.close()
            audio_bytes = b"".join(frames)
            return self._transcribe_whisper(audio_bytes)
        except Exception as e:
            logger.error(f"Whisper listen error: {e}")
            return None
        finally:
            stream.stop_stream(); stream.close()

    def _listen_vosk(self) -> Optional[str]:
        stream = self.audio.open(
            format=pyaudio.paInt16, channels=1, rate=self.config.sample_rate,
            input=True, frames_per_buffer=self.config.chunk_size,
        )
        recognizer = vosk.KaldiRecognizer(self.vosk_model, self.config.sample_rate)
        text_parts = []
        silence_counter = 0
        max_silence_chunks = int(self.config.silence_duration * self.config.sample_rate / self.config.chunk_size)
        try:
            logger.info("Listening (Vosk)...")
            while True:
                data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        return text
                else:
                    partial = json.loads(recognizer.PartialResult())
                    partial_text = partial.get("partial", "")
                    if partial_text:
                        text_parts = partial_text.split()
                        silence_counter = 0
                    else:
                        silence_counter += 1
                        if silence_counter >= max_silence_chunks and text_parts:
                            return " ".join(text_parts)
                if self.keyboard_command:
                    return None
        except KeyboardInterrupt:
            return None
        except Exception as e:
            logger.error(f"Vosk listen error: {e}")
            return None
        finally:
            stream.stop_stream(); stream.close()

    def speak(self, text: str):
        audio_bytes = self.synthesize(text)
        if audio_bytes:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_file = f.name
            try:
                with open(wav_file, "wb") as f:
                    f.write(audio_bytes)
                winsound.PlaySound(wav_file, winsound.SND_FILENAME)
            except Exception as e:
                logger.error(f"Speech playback failed: {e}")
            finally:
                if os.path.exists(wav_file):
                    os.unlink(wav_file)

    def pause(self):
        self.paused = True
        self._play_sound("pause")
        logger.info("Listening paused")

    def resume(self):
        self.paused = False
        self._play_sound("resume")
        logger.info("Listening resumed")

    # ---- Main Loop (CLI) ----

    def run(self):
        CLIAnimations.show_main_interface()
        CLIAnimations.show_startup_sequence()
        print_section("System Status")
        print_success(f"Language: {self.current_language.upper()}")
        print_success(f"STT Backend: {self.stt_backend.upper()}")
        print_success(f"Volume: {self.current_volume:.1f}")
        print_success(f"Speed: {self.current_speed:.2f}")
        print_success(f"Available Languages: {', '.join(self.get_available_languages())}")
        logger.info(f"AI Voice Chat started (STT: {self.stt_backend})")
        CLIAnimations.show_keyboard_shortcuts()
        if self.conversation_history:
            ChatDisplay.display_chat_history(self.conversation_history, max_messages=6)

        try:
            while True:
                if self.paused:
                    if self.keyboard_command == "quit":
                        print(f"\n{Colors.BRIGHT_RED}Goodbye!{Colors.RESET}")
                        break
                    elif self.keyboard_command == "resume":
                        self.resume()
                        self.keyboard_command = None
                else:
                    CLIAnimations.show_listening_prompt()
                    text = self.listen()

                    if text is None:
                        if self.keyboard_command:
                            self._process_keyboard_command()
                            if self.keyboard_command == "quit":
                                print(f"\n{Colors.BRIGHT_RED}Goodbye!{Colors.RESET}")
                                break
                            self.keyboard_command = None
                        else:
                            break
                    else:
                        self.add_to_conversation("user", text)
                        CLIAnimations.show_main_interface()
                        ChatDisplay.display_chat_history(self.conversation_history, max_messages=6)
                        CLIAnimations.show_processing_animation("Thinking...")
                        ai_response = self.chat_with_ai(text)
                        if ai_response:
                            self.add_to_conversation("assistant", ai_response)
                            CLIAnimations.show_main_interface()
                            ChatDisplay.display_chat_history(self.conversation_history, max_messages=6)
                            CLIAnimations.show_speaking_animation()
                            self.speak(ai_response)
        except KeyboardInterrupt:
            print(f"\n{Color.YELLOW}Interrupted.{Color.RESET}")
        finally:
            if self.conversation_history:
                try:
                    self.save_conversation(self.conversation_file)
                    print(f"{Color.GREEN}[AUTO-SAVED]{Color.RESET}")
                except Exception as e:
                    print(f"{Color.RED}[WARNING] Auto-save failed: {e}{Color.RESET}")
            keyboard.unhook_all()
            stop_window_monitoring()
            self.audio.terminate()
            self._show_stats()
            print(f"\n{Colors.BRIGHT_GREEN}VoiceChat stopped.{Colors.RESET}\n")
            logger.info("VoiceChat stopped.")

    def _process_keyboard_command(self):
        if not is_window_active():
            self.keyboard_command = None
            return
        cmd = self.keyboard_command
        if cmd == "quit":
            pass
        elif cmd == "pause":
            self.pause()
        elif cmd == "resume":
            self.resume()
        elif cmd == "english":
            self.switch_language("en")
        elif cmd == "persian":
            self.switch_language("fa")
        elif cmd == "languages":
            langs = ", ".join(self.get_available_languages())
            print(f"\n{Colors.BRIGHT_YELLOW}Languages: {langs}. Current: {self.current_language}{Colors.RESET}\n")
        elif cmd == "save":
            self.save_conversation()
        elif cmd == "stats":
            self._show_stats()
        elif cmd == "new":
            self.clear_conversation_history()
            CLIAnimations.show_main_interface()
            ChatDisplay.display_chat_history([], max_messages=6)
            print_success("New conversation started")
