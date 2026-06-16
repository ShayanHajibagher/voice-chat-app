#!/usr/bin/env python3
"""
Window Focus Detection for AI Voice Chat
Detects if the console window is minimized or not in focus
"""

import platform
import time
import threading
from typing import Callable, Optional

if platform.system() == "Windows":
    try:
        import ctypes
        from ctypes import wintypes

        # Windows API constants and functions
        SW_MINIMIZE = 6
        SW_RESTORE = 9

        # Get console window handle
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)

        GetConsoleWindow = kernel32.GetConsoleWindow
        GetConsoleWindow.restype = wintypes.HWND

        IsIconic = user32.IsIconic
        IsIconic.argtypes = [wintypes.HWND]
        IsIconic.restype = wintypes.BOOL

        GetForegroundWindow = user32.GetForegroundWindow
        GetForegroundWindow.restype = wintypes.HWND

        def is_window_minimized() -> bool:
            """Check if console window is minimized"""
            hwnd = GetConsoleWindow()
            if hwnd:
                return bool(IsIconic(hwnd))
            return False

        def is_window_focused() -> bool:
            """Check if console window is in focus (foreground)"""
            console_hwnd = GetConsoleWindow()
            foreground_hwnd = GetForegroundWindow()
            return console_hwnd == foreground_hwnd

        def get_window_focus_info() -> dict:
            """Get comprehensive window focus information"""
            minimized = is_window_minimized()
            focused = is_window_focused()

            return {
                "minimized": minimized,
                "focused": focused,
                "active": focused and not minimized,
            }

    except ImportError:
        print("Warning: Windows API not available, window focus detection disabled")

        def is_window_minimized() -> bool:
            return False

        def is_window_focused() -> bool:
            return True

        def get_window_focus_info() -> dict:
            return {"minimized": False, "focused": True, "active": True}

else:
    # For non-Windows systems, assume always active
    def is_window_minimized() -> bool:
        return False

    def is_window_focused() -> bool:
        return True

    def get_window_focus_info() -> dict:
        return {"minimized": False, "focused": True, "active": True}


class WindowFocusMonitor:
    """Monitors window focus state and triggers callbacks"""

    def __init__(self, check_interval: float = 0.5):
        self.check_interval = check_interval
        self.monitoring = False
        self.thread = None
        self.callbacks = {
            "minimized": [],
            "restored": [],
            "focused": [],
            "unfocused": [],
        }
        self.last_state = get_window_focus_info()

    def add_callback(self, event: str, callback: Callable):
        """Add callback for window state changes"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: Callable):
        """Remove callback for window state changes"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            current_state = get_window_focus_info()

            # Check for state changes
            if current_state["minimized"] != self.last_state["minimized"]:
                if current_state["minimized"]:
                    self._trigger_callbacks("minimized")
                else:
                    self._trigger_callbacks("restored")

            if current_state["focused"] != self.last_state["focused"]:
                if current_state["focused"]:
                    self._trigger_callbacks("focused")
                else:
                    self._trigger_callbacks("unfocused")

            self.last_state = current_state
            time.sleep(self.check_interval)

    def _trigger_callbacks(self, event: str):
        """Trigger all callbacks for an event"""
        for callback in self.callbacks[event]:
            try:
                callback()
            except Exception as e:
                print(f"Error in {event} callback: {e}")

    def start_monitoring(self):
        """Start monitoring window focus"""
        if not self.monitoring:
            self.monitoring = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop_monitoring(self):
        """Stop monitoring window focus"""
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def get_current_state(self) -> dict:
        """Get current window state"""
        return get_window_focus_info()


# Global monitor instance
_monitor = None


def get_window_monitor() -> WindowFocusMonitor:
    """Get or create global window monitor"""
    global _monitor
    if _monitor is None:
        _monitor = WindowFocusMonitor()
    return _monitor


def start_window_monitoring():
    """Start global window monitoring"""
    monitor = get_window_monitor()
    monitor.start_monitoring()
    return monitor


def stop_window_monitoring():
    """Stop global window monitoring"""
    global _monitor
    if _monitor:
        _monitor.stop_monitoring()
        _monitor = None


def is_window_active() -> bool:
    """Check if window is active (not minimized and focused)"""
    state = get_window_focus_info()
    return state["active"]


def on_window_minimized(callback: Callable):
    """Decorator/add function for minimized event"""
    monitor = get_window_monitor()
    monitor.add_callback("minimized", callback)


def on_window_restored(callback: Callable):
    """Decorator/add function for restored event"""
    monitor = get_window_monitor()
    monitor.add_callback("restored", callback)


def on_window_focused(callback: Callable):
    """Decorator/add function for focused event"""
    monitor = get_window_monitor()
    monitor.add_callback("focused", callback)


def on_window_unfocused(callback: Callable):
    """Decorator/add function for unfocused event"""
    monitor = get_window_monitor()
    monitor.add_callback("unfocused", callback)
