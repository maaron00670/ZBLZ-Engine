"""
ZBLZ Engine - Hotkeys Widget
Collapsible panel for assigning global hotkeys to speed control actions.
"""

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal

if TYPE_CHECKING:
    from services.hotkey_manager import HotkeyManager


class HotkeysWidget(QWidget):
    """
    Collapsible widget that lets the user bind global hotkeys to
    three speed control actions:

        • Aumentar x1  – increase speed by 1.0
        • Reset        – reset speed to 1.0
        • Disminuir x1 – decrease speed by 1.0

    Hotkeys fire even when the application window does not have focus.

    Signals:
        increase_requested: Emitted when the "Aumentar x1" hotkey fires.
        reset_requested:    Emitted when the "Reset" hotkey fires.
        decrease_requested: Emitted when the "Disminuir x1" hotkey fires.
    """

    increase_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    decrease_requested = pyqtSignal()

    # (action_id, display label)
    ACTIONS = [
        ("increase", "Aumentar x1"),
        ("reset",    "Reset"),
        ("decrease", "Disminuir x1"),
    ]

    _UNASSIGNED_TEXT = "Sin asignar"
    _CAPTURING_TEXT  = "Presiona una tecla..."

    def __init__(self, hotkey_manager: "HotkeyManager", parent=None):
        super().__init__(parent)
        self._hm = hotkey_manager
        self._key_buttons: dict[str, QPushButton] = {}
        self._active_capture: str | None = None

        self._setup_ui()
        if self._hm.is_available:
            self._connect_hotkey_signals()

    # ==================== UI Setup ====================

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        group = QGroupBox()
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(0)

        # ---- Toggle button ----
        self._toggle_btn = QPushButton("▶  Hotkeys globales")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(False)
        self._toggle_btn.setStyleSheet(
            "QPushButton { text-align: left; padding: 6px 10px; }"
        )
        self._toggle_btn.clicked.connect(self._toggle_content)
        group_layout.addWidget(self._toggle_btn)

        # ---- Collapsible content ----
        self._content = QFrame()
        self._content.setVisible(False)
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setSpacing(8)

        if not self._hm.is_available:
            warning = QLabel(
                "⚠  pynput no está instalado.\n"
                "Instálalo con:  pip install pynput"
            )
            warning.setObjectName("subtitle")
            warning.setAlignment(Qt.AlignCenter)
            content_layout.addWidget(warning)
        else:
            hint = QLabel(
                "Haz clic en un botón de tecla y luego presiona la tecla "
                "que quieras asignar."
            )
            hint.setObjectName("subtitle")
            hint.setWordWrap(True)
            content_layout.addWidget(hint)

            for action_id, action_label in self.ACTIONS:
                row = self._build_action_row(action_id, action_label)
                content_layout.addWidget(row)

        group_layout.addWidget(self._content)
        layout.addWidget(group)

    def _build_action_row(self, action_id: str, label_text: str) -> QWidget:
        """Build a single action row: [label] [stretch] [key button] [clear]"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        label = QLabel(label_text)
        label.setMinimumWidth(110)
        row_layout.addWidget(label)

        row_layout.addStretch()

        key_btn = QPushButton(self._UNASSIGNED_TEXT)
        key_btn.setMinimumWidth(140)
        key_btn.setMaximumWidth(180)
        key_btn.setToolTip("Haz clic para asignar una tecla")
        key_btn.clicked.connect(lambda _checked, aid=action_id: self._start_capture(aid))
        self._key_buttons[action_id] = key_btn
        row_layout.addWidget(key_btn)

        clear_btn = QPushButton("✕")
        clear_btn.setMaximumWidth(28)
        clear_btn.setToolTip("Quitar tecla asignada")
        clear_btn.clicked.connect(lambda _checked, aid=action_id: self._clear_binding(aid))
        row_layout.addWidget(clear_btn)

        return row

    # ==================== Interaction ====================

    def _toggle_content(self, checked: bool) -> None:
        self._content.setVisible(checked)
        arrow = "▼" if checked else "▶"
        self._toggle_btn.setText(f"{arrow}  Hotkeys globales")

    def _start_capture(self, action_id: str) -> None:
        """Put the widget into capture mode for the given action."""
        # If another button is already waiting, restore it.
        if self._active_capture and self._active_capture != action_id:
            self._cancel_capture_ui(self._active_capture)

        self._active_capture = action_id
        self._key_buttons[action_id].setText(self._CAPTURING_TEXT)
        self._hm.start_capture(action_id)

    def _clear_binding(self, action_id: str) -> None:
        """Remove the key binding for an action."""
        if self._active_capture == action_id:
            self._hm.cancel_capture()
            self._active_capture = None
        self._key_buttons[action_id].setText(self._UNASSIGNED_TEXT)
        self._hm.remove_binding(action_id)

    def _cancel_capture_ui(self, action_id: str) -> None:
        """Reset button text to the current binding (or unassigned)."""
        binding = self._hm.get_display_key(action_id)
        self._key_buttons[action_id].setText(
            binding if binding else self._UNASSIGNED_TEXT
        )

    # ==================== Signal Handling ====================

    def _connect_hotkey_signals(self) -> None:
        self._hm.hotkey_triggered.connect(self._on_hotkey_triggered)
        self._hm.key_captured.connect(self._on_key_captured)

    def _on_hotkey_triggered(self, action: str) -> None:
        """Dispatch the correct signal when a hotkey fires."""
        if action == "increase":
            self.increase_requested.emit()
        elif action == "reset":
            self.reset_requested.emit()
        elif action == "decrease":
            self.decrease_requested.emit()

    def _on_key_captured(self, action_id: str, key_str: str) -> None:
        """Update the button label after a successful key capture."""
        self._active_capture = None
        btn = self._key_buttons.get(action_id)
        if btn:
            btn.setText(key_str)
