"""
ZBLZ Engine - Hotkey Manager
Global keyboard listener for speed control hotkeys.

Uses pynput to capture key events system-wide, so hotkeys fire
even when the application window does not have focus.
"""

import threading
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

try:
    from pynput import keyboard as pynput_keyboard
    _PYNPUT_AVAILABLE = True
except ImportError:
    _PYNPUT_AVAILABLE = False


class HotkeyManager(QObject):
    """
    Manages global hotkeys using pynput.

    Runs a background keyboard listener thread and emits Qt signals
    when registered keys are pressed or when a key capture completes,
    keeping UI updates safely on the main thread.

    Signals:
        hotkey_triggered(str): Emitted with the action name when a
            registered hotkey is pressed.
        key_captured(str, str): Emitted with (action_name, display_str)
            after a capture-mode key press completes.
    """

    hotkey_triggered = pyqtSignal(str)
    key_captured = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bindings: dict[str, str] = {}   # canonical_str -> action_name
        self._capture_action: Optional[str] = None
        self._listener = None
        self._lock = threading.Lock()
        self._available = _PYNPUT_AVAILABLE

        if self._available:
            self._start_listener()

    # ==================== Public API ====================

    @property
    def is_available(self) -> bool:
        """True if pynput is installed and the listener is running."""
        return self._available

    def start_capture(self, action_name: str) -> None:
        """Enter capture mode: the next key press will be bound to action_name."""
        with self._lock:
            self._capture_action = action_name

    def cancel_capture(self) -> None:
        """Cancel any ongoing key capture without changing bindings."""
        with self._lock:
            self._capture_action = None

    def remove_binding(self, action_name: str) -> None:
        """Remove the key binding for the given action."""
        with self._lock:
            self._bindings = {
                k: v for k, v in self._bindings.items() if v != action_name
            }

    def get_display_key(self, action_name: str) -> Optional[str]:
        """Return the display string for the key bound to action_name, or None."""
        with self._lock:
            for key_str, action in self._bindings.items():
                if action == action_name:
                    return key_str
        return None

    def stop(self) -> None:
        """Stop the background keyboard listener."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass

    # ==================== Internal ====================

    def _start_listener(self) -> None:
        """Start pynput listener in a daemon thread."""
        try:
            self._listener = pynput_keyboard.Listener(
                on_press=self._on_key_press
            )
            self._listener.daemon = True
            self._listener.start()
        except Exception:
            self._available = False

    def _on_key_press(self, key) -> None:
        """Called by pynput (background thread) on every key press."""
        canonical = self._key_to_canonical(key)
        display = self._key_to_display(key)

        with self._lock:
            capture_action = self._capture_action
            if capture_action is not None:
                # Capture mode: bind this key to the pending action.
                self._capture_action = None
                # Remove any existing binding for this action.
                self._bindings = {
                    k: v for k, v in self._bindings.items()
                    if v != capture_action
                }
                # One key can only trigger one action; remove conflicting entry.
                self._bindings.pop(canonical, None)
                self._bindings[canonical] = capture_action
                # Signal is emitted outside the lock to avoid deadlock.
                action_for_signal = capture_action
                display_for_signal = display
            else:
                action_for_signal = self._bindings.get(canonical)
                display_for_signal = None

        if display_for_signal is not None:
            # Emit key_captured signal (queued cross-thread, safe for Qt).
            self.key_captured.emit(action_for_signal, display_for_signal)
        elif action_for_signal:
            self.hotkey_triggered.emit(action_for_signal)

    @staticmethod
    def _key_to_canonical(key) -> str:
        """Stable lowercase string used as dict key."""
        try:
            if hasattr(key, "char") and key.char is not None:
                return key.char.lower()
        except Exception:
            pass
        return str(key)

    @staticmethod
    def _key_to_display(key) -> str:
        """Human-readable string shown on the button."""
        try:
            if hasattr(key, "char") and key.char is not None:
                return key.char.upper()
            # e.g. "Key.f5" -> "F5", "Key.space" -> "Space"
            name = str(key).replace("Key.", "")
            return name.capitalize()
        except Exception:
            return str(key)
