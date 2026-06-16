#!/usr/bin/env python3
"""
Professional CLI for AI Voice Chat Application
"""

import argparse
import sys
import os
import json
from typing import Optional
from animations import *


# These functions are now imported from animations.py


def validate_config(config_path: str) -> bool:
    """Validate configuration file"""
    if not os.path.exists(config_path):
        print_error(f"Configuration file not found: {config_path}")
        return False

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        required_keys = ["languages", "api_url", "sample_rate", "chunk_size"]
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            print_error(f"Missing required keys in config: {', '.join(missing_keys)}")
            return False

        return True
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print_error(f"Error reading config: {e}")
        return False


def list_models(config_path: str = "config.json"):
    """List available models for all languages"""
    if not validate_config(config_path):
        sys.exit(1)

    with open(config_path, "r") as f:
        config = json.load(f)

    print_section("Available Models")

    for lang_code, lang_config in config["languages"].items():
        lang_name = {"en": "English", "fa": "Persian (Farsi)"}.get(
            lang_code, lang_code.upper()
        )

        print()
        print(f"{Colors.BOLD}Language: {lang_name}{Colors.RESET}")
        print(f"  Code: {lang_code}")
        print(f"  Vosk Model: {lang_config['vosk_model_path']}")
        print(f"  TTS Model:    {lang_config['model_path']}")
        print(f"  TTS Config:   {lang_config['config_path']}")

        if os.path.exists(lang_config["vosk_model_path"]):
            print_success(f"Vosk model available")
        else:
            print_error(f"Vosk model NOT FOUND")

        if os.path.exists(lang_config["model_path"]):
            print_success(f"TTS model available")
        else:
            print_error(f"TTS model NOT FOUND")

    print()


def show_config(config_path: str = "config.json"):
    """Show current configuration"""
    if not validate_config(config_path):
        sys.exit(1)

    with open(config_path, "r") as f:
        config = json.load(f)

    print_section("Current Configuration")

    print(f"  Config File:   {config_path}")
    print(f"  Language:      {config.get('language', 'Not set').upper()}")
    print(f"  API URL:       {config.get('api_url', 'Not set')}")
    print(f"  API Timeout:   {config.get('api_timeout', 'Not set')}s")
    print(f"  Sample Rate:   {config.get('sample_rate', 'Not set')} Hz")
    print(f"  Chunk Size:    {config.get('chunk_size', 'Not set')}")
    print(f"  Max Tokens:    {config.get('max_tokens', 'Not set')}")
    print(f"  Temperature:    {config.get('temperature', 'Not set')}")
    print(f"  Silence Duration: {config.get('silence_duration', 'Not set')}s")

    print_section("Audio Synthesis Settings")
    synth = config.get("synth", {})
    print(f"  Volume:        {synth.get('volume', 1.0)}")
    print(f"  Length Scale:  {synth.get('length_scale', 1.0)}")
    print(f"  Noise Scale:   {synth.get('noise_scale', 0.667)}")
    print(f"  Noise W Scale: {synth.get('noise_w_scale', 0.8)}")
    print(f"  Normalize:     {synth.get('normalize_audio', False)}")

    print_section("Language Configuration")
    for lang_code, lang_config in config["languages"].items():
        lang_name = {"en": "English", "fa": "Persian (Farsi)"}.get(
            lang_code, lang_code.upper()
        )
        marker = " (current)" if lang_code == config.get("language") else ""
        print(f"  {lang_name}{marker}:")
        print(f"    Vosk: {lang_config['vosk_model_path']}")
        print(f"    TTS:   {lang_config['model_path']}")

    print()


def test_setup(config_path: str = "config.json"):
    """Test all components of the voice chat system"""
    print_section("System Test")

    if not validate_config(config_path):
        return False

    with open(config_path, "r") as f:
        config = json.load(f)

    results = []

    print("Checking dependencies...")
    try:
        import vosk

        print_success("vosk installed")
        results.append(True)
    except ImportError:
        print_error("vosk NOT installed")
        print_info("Install with: pip install vosk")
        results.append(False)

    try:
        import requests

        print_success("requests installed")
        results.append(True)
    except ImportError:
        print_error("requests NOT installed")
        print_info("Install with: pip install requests")
        results.append(False)

    try:
        import pyaudio

        print_success("pyaudio installed")
        results.append(True)
    except ImportError:
        print_error("pyaudio NOT installed")
        print_info("Install with: pipwin install pyaudio (Windows)")
        results.append(False)

    try:
        from piper import PiperVoice

        print_success("piper-tts installed")
        results.append(True)
    except ImportError:
        print_error("piper-tts NOT installed")
        print_info("Install with: pip install piper-tts")
        results.append(False)

    print()
    print("Checking model files...")

    for lang_code, lang_config in config["languages"].items():
        vosk_exists = os.path.exists(lang_config["vosk_model_path"])
        tts_exists = os.path.exists(lang_config["model_path"])
        config_exists = os.path.exists(lang_config["config_path"])

        if vosk_exists and tts_exists and config_exists:
            print_success(f"{lang_code.upper()}: All models present")
            results.append(True)
        else:
            missing = []
            if not vosk_exists:
                missing.append("Vosk")
            if not tts_exists:
                missing.append("TTS")
            if not config_exists:
                missing.append("TTS Config")
            print_warning(f"{lang_code.upper()}: Missing {', '.join(missing)}")
            results.append(False)

    print()
    print_section("Test Results")

    if all(results):
        print_success("All tests passed! System is ready to use.")
        print_info("Run: python voice_chat.py")
        return True
    else:
        failed = len([r for r in results if not r])
        print_error(f"{failed} test(s) failed")
        print_info("Fix the issues above and try again.")
        return False


def start_interactive(conversation_options=None, language_override=None):
    """Start the voice chat application with beautiful animations"""
    try:
        from voice_chat import VoiceChat, VoiceChatConfig
    except ImportError as e:
        CLIAnimations.show_error_alert(f"Failed to import voice_chat: {e}")
        sys.exit(1)

    LANG_MAP = {
        "en": "en",
        "english": "en",
        "fa": "fa",
        "persian": "fa",
    }

    # Show welcome banner
    CLIAnimations.show_welcome_banner()

    # Show startup sequence with spinners
    CLIAnimations.show_startup_sequence()

    # Load configuration
    config = VoiceChatConfig()

    # Apply language override from CLI flag (session only, no config.json write)
    if language_override:
        mapped = LANG_MAP.get(language_override)
        if mapped and config.set_language(mapped):
            print_info(f"Language overridden to: {mapped.upper()} (this session)")

    # Show system information with animations
    print_section("System Status")
    print_success(f"Language: {config.language.upper()}")
    print_success(
        f"Available: {', '.join([k.upper() for k in config.languages.keys()])}"
    )
    print_info(f"API Endpoint: {config.api_url}")

    # Show features
    CLIAnimations.show_feature_highlights()

    # Show keyboard shortcuts
    CLIAnimations.show_keyboard_shortcuts()

    try:
        chat = VoiceChat(config, conversation_options)
        chat.run()
    except KeyboardInterrupt:
        print_warning("\n👋 Interrupted by user - Goodbye!")
        sys.exit(0)
    except Exception as e:
        CLIAnimations.show_error_alert(f"Application Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="voice_chat",
        description="AI Voice Chat v2.2 - Multi-language Voice Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                            Start web UI (default)
  python cli.py --language fa              Start web UI with Persian
  python cli.py --cli                      Start terminal CLI mode
  python cli.py --list-models              List available models
  python cli.py --config custom.json       Use custom config file
  python cli.py --test                     Test system setup
        """,
    )

    parser.add_argument(
        "--language",
        "-l",
        choices=["en", "fa", "english", "persian"],
        help="Set language for this session (en, fa, english, persian)",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )

    parser.add_argument(
        "--list-models",
        "-m",
        action="store_true",
        help="List available models for all languages",
    )

    parser.add_argument(
        "--show-config", "-s", action="store_true", help="Display current configuration"
    )

    parser.add_argument(
        "--test",
        "-t",
        action="store_true",
        help="Test system setup (dependencies, models, config)",
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument(
        "--load-conversation",
        "-L",
        type=str,
        help="Load conversation from specific JSON file",
    )

    parser.add_argument(
        "--fresh",
        "-F",
        action="store_true",
        help="Start with fresh conversation (ignore saved)",
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Start in terminal CLI mode instead of web UI",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=5000,
        help="Port for web server (default: 5000)",
    )

    args = parser.parse_args()

    if args.no_color:
        for color in dir(Colors):
            if not color.startswith("_"):
                setattr(Colors, color, "")

    # Handle conversation loading options
    conversation_options = {}
    if args.load_conversation:
        conversation_options["load_file"] = args.load_conversation
    if args.fresh:
        conversation_options["fresh"] = True

    if args.list_models:
        list_models(args.config)
        sys.exit(0)

    if args.show_config:
        show_config(args.config)
        sys.exit(0)

    if args.test:
        success = test_setup(args.config)
        sys.exit(0 if success else 1)

    if args.cli:
        start_interactive(conversation_options, language_override=args.language)
    else:
        # Default: web UI mode
        if args.language:
            LANG_MAP = {"en": "en", "english": "en", "fa": "fa", "persian": "fa"}
            mapped = LANG_MAP.get(args.language)
            if mapped:
                if os.path.exists(args.config):
                    with open(args.config, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    cfg_data["language"] = mapped
                    with open(args.config, "w", encoding="utf-8") as f:
                        json.dump(cfg_data, f, indent=2)

        try:
            from web_server import socketio, app

            import webbrowser
            webbrowser.open(f"http://localhost:{args.port}")

            print_info(f"AI Voice Chat running at http://localhost:{args.port}")
            print_info("Press Ctrl+C to stop the server")
            socketio.run(app, host="0.0.0.0", port=args.port, debug=False)
        except ImportError as e:
            CLIAnimations.show_error_alert(f"Failed to import web_server: {e}")
            print_info("Make sure web dependencies are installed:")
            print_info("pip install flask flask-socketio python-socketio eventlet")
            sys.exit(1)


if __name__ == "__main__":
    main()
