#!/usr/bin/env python3
"""
Advanced CLI Animations and Visual Effects for AI Voice Chat
"""

import sys
import time
import threading
import os
from typing import Optional, Callable


class Colors:
    """Enhanced ANSI color codes with gradients and effects"""

    # Basic colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Custom gradients
    @staticmethod
    def gradient_text(
        text: str, start_color: str, end_color: Optional[str] = None
    ) -> str:
        """Create gradient text effect"""
        if not end_color:
            end_color = start_color
        return f"{start_color}{text}{Colors.RESET}"

    @staticmethod
    def pulse_text(text: str, color: str) -> str:
        """Create pulsing text effect"""
        return f"{color}{Colors.BLINK}{text}{Colors.RESET}"

    @staticmethod
    def rainbow_text(text: str) -> str:
        """Create rainbow colored text"""
        colors = [
            Colors.RED,
            Colors.YELLOW,
            Colors.GREEN,
            Colors.CYAN,
            Colors.BLUE,
            Colors.MAGENTA,
        ]
        result = ""
        for i, char in enumerate(text):
            result += f"{colors[i % len(colors)]}{char}"
        result += Colors.RESET
        return result


class Spinner:
    """Animated spinner for loading states"""

    def __init__(self, message: str = "Loading", spinner_chars: Optional[list] = None):
        self.message = message
        self.spinner_chars = spinner_chars or ["|", "/", "-", "\\", "|", "/", "-", "\\"]
        self.running = False
        self.thread = None

    def _spin(self):
        """Spinner animation loop"""
        i = 0
        while self.running:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            sys.stdout.write(f"\r{Colors.CYAN}{char}{Colors.RESET} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        """Start the spinner"""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self, success: bool = True):
        """Stop the spinner"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)

        # Clear the line
        sys.stdout.write(f"\r{' ' * (len(self.message) + 3)}\r")

        if success:
            sys.stdout.write(
                f"{Colors.BRIGHT_GREEN}[OK]{Colors.RESET} {self.message}\n"
            )
        else:
            sys.stdout.write(
                f"{Colors.BRIGHT_RED}[FAIL]{Colors.RESET} {self.message}\n"
            )
        sys.stdout.flush()


class ProgressBar:
    """Animated progress bar"""

    def __init__(self, total: int, width: int = 50, prefix: str = "Progress"):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.current = 0

    def update(self, current: int):
        """Update progress bar"""
        self.current = current
        percentage = int((current / self.total) * 100)
        filled = int((current / self.total) * self.width)

        bar = "█" * filled + "░" * (self.width - filled)
        sys.stdout.write(
            f"\r{Colors.CYAN}{self.prefix}: {Colors.RESET}[{Colors.BRIGHT_BLUE}{bar}{Colors.RESET}] {percentage}% ({current}/{self.total})"
        )
        sys.stdout.flush()

        if current >= self.total:
            sys.stdout.write("\n")

    def complete(self):
        """Mark as complete"""
        self.update(self.total)


class TypingEffect:
    """Typing animation effect"""

    @staticmethod
    def type_text(text: str, delay: float = 0.05, color: str = Colors.WHITE):
        """Animate text as if being typed"""
        for char in text:
            sys.stdout.write(f"{color}{char}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write("\n")

    @staticmethod
    def reveal_text(text: str, delay: float = 0.1, color: str = Colors.CYAN):
        """Reveal text character by character"""
        for char in text:
            sys.stdout.write(f"{color}{char}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(delay)


class WaveAnimation:
    """Wave-like animation effect"""

    @staticmethod
    def wave_text(text: str, waves: int = 1):
        """Create a wave effect with text"""
        for wave in range(waves):
            for i in range(len(text)):
                line = ""
                for j, char in enumerate(text):
                    if j == i:
                        line += f"{Colors.BRIGHT_CYAN}{Colors.BOLD}{char}{Colors.RESET}"
                    else:
                        line += f"{Colors.DIM}{char}{Colors.RESET}"
                sys.stdout.write(f"\r{line}")
                sys.stdout.flush()
                time.sleep(0.1)
            time.sleep(0.2)
        sys.stdout.write(f"\r{Colors.BRIGHT_CYAN}{Colors.BOLD}{text}{Colors.RESET}\n")


class StatusDisplay:
    """Enhanced status display with animations"""

    def __init__(self):
        self.current_status = None
        self.status_icons = {
            "LISTENING": "[LISTEN]",
            "PROCESSING": "[PROC]",
            "SPEAKING": "[SPEAK]",
            "PAUSED": "[PAUSE]",
            "READY": "[READY]",
            "ERROR": "[ERROR]",
            "LOADING": "[LOAD]",
        }

    def show_status(self, status: str, message: str = "", color: str = Colors.CYAN):
        """Display animated status"""
        if status != self.current_status:
            self.current_status = status
            icon = self.status_icons.get(status, "ℹ️")

            # Clear previous line
            sys.stdout.write(f"\r{' ' * 80}\r")

            # Show new status with animation
            status_text = f"{icon} {status}"
            if message:
                status_text += f": {message}"

            # Pulse effect for important statuses
            if status in ["SPEAKING", "PROCESSING"]:
                sys.stdout.write(f"{Colors.BLINK}{color}{status_text}{Colors.RESET}")
            else:
                sys.stdout.write(f"{color}{status_text}{Colors.RESET}")

            sys.stdout.flush()

    def clear_status(self):
        """Clear current status display"""
        sys.stdout.write(f"\r{' ' * 80}\r")
        self.current_status = None


class ChatDisplay:
    """Beautiful chat message display system"""

    @staticmethod
    def format_message(message, role, max_width=70):
        """Format a single chat message"""
        lines = []
        content = message["content"]
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        # Wrap text to max_width
        words = content.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= max_width:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        return lines, timestamp

    @staticmethod
    def display_chat_message(message, role, show_timestamp=True):
        """Display a single chat message in a beautiful box"""
        lines, timestamp = ChatDisplay.format_message(message, role)

        # Colors and styles
        if role == "user":
            box_color = Colors.BRIGHT_BLUE
            name_color = Colors.BRIGHT_CYAN
            name = "You"
            align = "right"
            corner_char = "╭"
            side_char = "│"
            bottom_corner = "╰"
        else:
            box_color = Colors.BRIGHT_GREEN
            name_color = Colors.BRIGHT_MAGENTA
            name = "AI Assistant"
            align = "left"
            corner_char = "╭"
            side_char = "│"
            bottom_corner = "╰"

        # Header
        header = f" {name} "
        print(f"{box_color}+{'-' * (len(header) + 2)}+")
        print(
            f"{box_color}|{Colors.RESET} {name_color}{Colors.BOLD}{header}{Colors.RESET} {box_color}|"
        )

        # Timestamp
        if show_timestamp:
            time_str = f" {timestamp} "
            print(f"{box_color}+{'-' * (len(time_str) + 2)}+")
            print(
                f"{box_color}|{Colors.RESET} {Colors.DIM}{time_str}{Colors.RESET} {box_color}|"
            )

        # Message content
        print(f"{box_color}+{'-' * 72}+")

        for line in lines:
            if align == "left":
                padding = 70 - len(line)
                print(f"{box_color}|{Colors.RESET} {line}{' ' * padding} {box_color}|")
            else:
                padding = 70 - len(line)
                print(f"{box_color}|{' ' * padding}{line} {Colors.RESET}{box_color}|")

        # Bottom
        print(f"{box_color}+{'-' * 72}+{Colors.RESET}")
        print()

    @staticmethod
    def display_chat_history(conversation_history, max_messages=8):
        """Display recent chat history in a centered, auto-scrolling format"""
        if not conversation_history:
            # Center the "no history" message
            terminal_width = 80
            try:
                terminal_width = os.get_terminal_size().columns
            except:
                terminal_width = 80

            no_history_msg = "No conversation history yet."
            padding = (terminal_width - len(no_history_msg)) // 2
            print(f"{Colors.DIM}{' ' * padding}{no_history_msg}{Colors.RESET}\n")
            return

        # Auto-scroll: show only recent messages
        recent_messages = (
            conversation_history[-max_messages:]
            if len(conversation_history) > max_messages
            else conversation_history
        )

        # Only show scroll indicator if there are more messages
        if len(conversation_history) > max_messages:
            terminal_width = 80
            try:
                terminal_width = os.get_terminal_size().columns
            except:
                terminal_width = 80

            scroll_msg = f"^ {len(conversation_history) - max_messages} older messages"
            padding = (terminal_width - len(scroll_msg)) // 2
            print(f"{Colors.DIM}{' ' * padding}{scroll_msg}{Colors.RESET}\n")

        # Display messages centered (auto-scrolling by showing only recent)
        for message in recent_messages:
            ChatDisplay.display_centered_message(
                message, message["role"], show_timestamp=False
            )

    @staticmethod
    def display_centered_message(message, role, show_timestamp=True):
        """Display a single chat message centered in the terminal"""
        # Get terminal width for centering
        terminal_width = 80
        try:
            terminal_width = os.get_terminal_size().columns
        except:
            terminal_width = 80

        # Calculate box width (responsive to terminal size)
        box_width = min(74, terminal_width - 6)  # Leave margin
        content_width = box_width - 4  # Account for borders

        # Colors and styles
        if role == "user":
            box_color = Colors.BRIGHT_BLUE
            name_color = Colors.BRIGHT_CYAN
            name = "You"
            align = "right"  # User messages right-aligned
        else:
            box_color = Colors.BRIGHT_GREEN
            name_color = Colors.BRIGHT_MAGENTA
            name = "AI Assistant"
            align = "left"  # AI messages left-aligned

        # Format timestamp
        import time

        timestamp = time.strftime("%H:%M:%S", time.localtime())

        # Header - centered
        header = f" {name} "
        header_padding = (box_width - len(header) - 2) // 2
        header_line = f"{box_color}+{'-' * header_padding}{header}{' ' * (box_width - len(header) - header_padding - 2)}+"

        # Center the entire box
        box_padding = (terminal_width - box_width) // 2
        prefix = " " * box_padding

        print(f"{prefix}{header_line}")

        # Timestamp - centered
        if show_timestamp:
            time_str = f" {timestamp} "
            time_padding = (box_width - len(time_str) - 2) // 2
            time_line = f"{box_color}+{'-' * time_padding}{time_str}{' ' * (box_width - len(time_str) - time_padding - 2)}+"
            print(f"{prefix}{time_line}")

        # Content separator - centered
        content_separator = f"{box_color}+{'-' * (box_width - 2)}+"
        print(f"{prefix}{content_separator}")

        # Message content with proper alignment
        wrapped_lines = ChatDisplay.wrap_text(message["content"], content_width - 2)

        for line in wrapped_lines:
            if align == "left":
                # AI messages left-aligned
                content_line = f"{box_color}|{Colors.RESET} {line}{' ' * (content_width - len(line) - 1)} {box_color}|"
            else:
                # User messages right-aligned
                content_line = f"{box_color}|{' ' * (content_width - len(line) - 1)}{line} {Colors.RESET}{box_color}|"
            print(f"{prefix}{content_line}")

        # Bottom - centered
        bottom_line = f"{box_color}+{'-' * (box_width - 2)}+"
        print(f"{prefix}{bottom_line}{Colors.RESET}")
        print()

    @staticmethod
    def wrap_text(text, max_width):
        """Wrap text to fit within max_width"""
        if not text:
            return [""]

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + " " + word) <= max_width:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    @staticmethod
    def display_current_message(message, role, animated=True):
        """Display the current message being processed"""
        if animated and role == "assistant":
            # Thinking animation for AI responses
            terminal_width = 80
            try:
                terminal_width = os.get_terminal_size().columns
            except:
                terminal_width = 80

            thinking_msg = "[AI] Thinking..."
            padding = (terminal_width - len(thinking_msg)) // 2
            print(f"{Colors.BRIGHT_MAGENTA}{' ' * padding}{thinking_msg}{Colors.RESET}")
            time.sleep(0.8)

        ChatDisplay.display_centered_message(message, role)

    @staticmethod
    def show_conversation_stats(stats):
        """Display conversation statistics in a nice box"""
        print(
            f"{Colors.BRIGHT_YELLOW}{Colors.BOLD}:: Conversation Statistics ::{Colors.RESET}"
        )
        print(f"{Colors.BRIGHT_YELLOW}{'=' * 40}{Colors.RESET}")

        elapsed = stats.get("elapsed_time", 0)
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        stats_items = [
            ("User Messages", stats.get("user_messages", 0)),
            ("AI Messages", stats.get("ai_messages", 0)),
            ("Words Spoken", stats.get("words_spoken", 0)),
            ("Session Time", f"{minutes}m {seconds}s"),
            ("Language", stats.get("language", "Unknown").upper()),
            ("Volume", f"{stats.get('volume', 1.0):.1f}"),
            ("Speed", f"{stats.get('speed', 1.0):.2f}"),
        ]

        for label, value in stats_items:
            print(
                f"  {Colors.CYAN}{label:15}{Colors.RESET}: {Colors.WHITE}{value}{Colors.RESET}"
            )

        print()


class CLIAnimations:
    """Collection of CLI animation utilities"""

    @staticmethod
    def show_welcome_banner():
        """Animated welcome banner"""
        banner_lines = [
            "+===============================================================+",
            "|            CYAN DIAMOND STUDIO - AI VOICE CHAT v4.6           |",
            "|                Advanced Voice Assistant with AI               |",
            "|             Powered by Cyan Diamond Studio                    |",
            "+===============================================================+",
        ]

        print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}")
        for line in banner_lines:
            print(line)
        print(Colors.RESET)

    @staticmethod
    def show_startup_sequence():
        """Animated startup sequence"""
        steps = [
            ("Initializing configuration", 0.5),
            ("Loading language models", 1.0),
            ("Setting up audio systems", 0.8),
            ("Preparing voice synthesis", 0.6),
            ("Ready for conversation", 0.3),
        ]

        for message, delay in steps:
            spinner = Spinner(message)
            spinner.start()
            time.sleep(delay)
            spinner.stop()

    @staticmethod
    def show_feature_highlights():
        """Highlight key features with animations"""
        features = [
            "[+] Advanced Voice Recognition",
            "[+] Persistent AI Memory",
            "[+] Multi-language Support",
            "[+] Real-time Processing",
            "[+] Beautiful CLI Interface",
        ]

        print(
            f"\n{Colors.BRIGHT_YELLOW}{Colors.BOLD}:: Key Features ::{Colors.RESET}\n"
        )

        for feature in features:
            WaveAnimation.wave_text(feature)
            time.sleep(0.3)

    @staticmethod
    def show_keyboard_shortcuts():
        """Animated keyboard shortcuts display"""
        shortcuts = [
            ("Q/ESC", "Quit application", "🚪"),
            ("P", "Pause listening", "⏸️"),
            ("R", "Resume listening", "▶️"),
            ("E/F", "Switch language", "🌐"),
            ("S", "Save conversation", "💾"),
            ("N", "New conversation", "🆕"),
            ("T", "Show statistics", "📊"),
            ("UP/DOWN", "Adjust volume", "🔊"),
            ("LEFT/RIGHT", "Adjust speed", "⚡"),
        ]

        print(
            f"\n{Colors.BRIGHT_MAGENTA}{Colors.BOLD}🎮 Keyboard Shortcuts{Colors.RESET}"
        )
        print(f"{Colors.BRIGHT_MAGENTA}{'═' * 50}{Colors.RESET}\n")

        for key, desc, icon in shortcuts:
            print(
                f"  {Colors.CYAN}{key:10}{Colors.RESET} - {Colors.WHITE}{desc:20}{Colors.RESET} {icon}"
            )
            time.sleep(0.03)

        print(
            f"\n{Colors.DIM}💡 Tip: Minimize window to disable keyboard shortcuts{Colors.RESET}\n"
        )

    @staticmethod
    def show_status_panel(current_status, stats):
        """Display a compact status panel"""
        status_icon = {
            "LISTENING": "🎤",
            "PROCESSING": "⚡",
            "SPEAKING": "🔊",
            "PAUSED": "⏸️",
            "READY": "✅",
            "ERROR": "❌",
            "LOADING": "⏳",
        }.get(current_status, "ℹ️")

        # Create status line
        status_line = f"{status_icon} {current_status}"
        messages = stats.get("user_messages", 0) + stats.get("ai_messages", 0)

        print(
            f"\r{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD} STATUS {Colors.RESET} {Colors.BRIGHT_BLUE}{status_line}{Colors.RESET} | {Colors.CYAN}Messages: {messages}{Colors.RESET} | {Colors.GREEN}Lang: {stats.get('language', 'EN').upper()}{Colors.RESET}",
            end="",
            flush=True,
        )

    @staticmethod
    def clear_status_panel():
        """Clear the status panel"""
        print(f"\r{' ' * 100}\r", end="", flush=True)

    @staticmethod
    def show_main_interface():
        """Display the centered main chat interface layout"""
        # Clear screen
        os.system("cls" if os.name == "nt" else "clear")

        # Get terminal width for centering
        terminal_width = 80  # Default width

        try:
            terminal_width = os.get_terminal_size().columns
        except:
            terminal_width = 80

        # Center the header
        header = "🤖 AI VOICE CHAT v4.6"
        header_padding = (terminal_width - len(header) - 4) // 2
        top_border = "╔" + "═" * (terminal_width - 2) + "╗"
        header_line = (
            "║"
            + " " * header_padding
            + header
            + " " * (terminal_width - len(header) - header_padding - 2)
            + "║"
        )
        bottom_border = "╚" + "═" * (terminal_width - 2) + "╝"

        print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}")
        print(top_border)
        print(header_line)
        print(bottom_border)
        print(Colors.RESET)

        # Show conversation area with centered title
        chat_title = "💬 Conversation"
        title_padding = (terminal_width - len(chat_title) - 4) // 2
        print(
            f"{Colors.BRIGHT_YELLOW}{Colors.BOLD}{' ' * title_padding}{chat_title}{Colors.RESET}"
        )
        print(f"{Colors.BRIGHT_YELLOW}{'─' * (terminal_width - 2)}{Colors.RESET}\n")

    @staticmethod
    def show_listening_prompt():
        """Show animated listening prompt"""
        prompts = [
            f"{Colors.BRIGHT_GREEN}🎤 Listening... Speak now!{Colors.RESET}",
            f"{Colors.BRIGHT_GREEN}🎤 I'm listening...{Colors.RESET}",
            f"{Colors.BRIGHT_GREEN}🎤 Ready for your voice!{Colors.RESET}",
        ]

        for prompt in prompts:
            print(f"\r{prompt}", end="", flush=True)
            time.sleep(0.8)

    @staticmethod
    def show_processing_animation(message="Processing"):
        """Show processing animation"""
        spinner = Spinner(f"🤖 {message}")
        spinner.start()
        time.sleep(1.5)  # Simulate processing time
        spinner.stop(success=True)

    @staticmethod
    def show_speaking_animation():
        """Show speaking animation"""
        print(f"{Colors.BRIGHT_MAGENTA}🔊 Speaking...{Colors.RESET}")
        time.sleep(0.5)

    @staticmethod
    def show_conversation_loaded(messages_count: int):
        """Animate conversation loading"""
        print(f"\n{Colors.BRIGHT_BLUE}Loading previous conversation...{Colors.RESET}")
        progress = ProgressBar(messages_count, prefix="Messages")
        for i in range(messages_count + 1):
            progress.update(i)
            time.sleep(0.02)
        print(
            f"{Colors.BRIGHT_GREEN}✓ Conversation loaded with {messages_count} messages!{Colors.RESET}\n"
        )

    @staticmethod
    def show_error_alert(message: str):
        """Animated error alert"""
        print(
            f"\n{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD} ERROR {Colors.RESET} {Colors.BRIGHT_RED}{message}{Colors.RESET}\n"
        )

    @staticmethod
    def show_success_alert(message: str):
        """Animated success alert"""
        print(f"{Colors.BRIGHT_GREEN}✓ {message}{Colors.RESET}")

    @staticmethod
    def create_loading_bar(width: int = 50):
        """Create a simple loading bar"""
        return "█" * width


# Convenience functions for easy use
def loading_spinner(message: str) -> Spinner:
    """Create and return a loading spinner"""
    return Spinner(message)


def progress_bar(total: int, width: int = 50, prefix: str = "Progress") -> ProgressBar:
    """Create and return a progress bar"""
    return ProgressBar(total, width, prefix)


def status_display() -> StatusDisplay:
    """Create and return a status display"""
    return StatusDisplay()


# Backwards compatibility with existing code
def print_header(text: str):
    print(f"{Colors.BRIGHT_MAGENTA}{Colors.BOLD}{text}{Colors.RESET}")


def print_success(text: str):
    print(f"{Colors.BRIGHT_GREEN}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.BRIGHT_RED}[ERROR] {text}{Colors.RESET}", file=sys.stderr)


def print_warning(text: str):
    print(f"{Colors.BRIGHT_YELLOW}⚠ {text}{Colors.RESET}", file=sys.stderr)


def print_info(text: str):
    print(f"{Colors.BRIGHT_BLUE}ℹ {text}{Colors.RESET}")


def print_section(title: str):
    width = 60
    print()
    print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}{'═' * width}{Colors.RESET}")
    print(
        f"{Colors.BRIGHT_CYAN}{Colors.BOLD}║{Colors.RESET} {Colors.BRIGHT_WHITE}{Colors.BOLD}{title.center(width - 4)}{Colors.RESET} {Colors.BRIGHT_CYAN}{Colors.BOLD}║{Colors.RESET}"
    )
    print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}{'═' * width}{Colors.RESET}")
    print()
