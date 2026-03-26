"""
ZBLZ Engine - Command Output Widget
Displays generated launch commands and supports launching non-Steam programs.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QGroupBox, QCheckBox,
    QLineEdit, QApplication
)
from PyQt5.QtCore import pyqtSignal, QTimer


class CommandOutputWidget(QWidget):
    """
    Widget for displaying and copying generated launch commands.

    Features:
    - Steam launch option generation
    - Copy to clipboard button
    - Optional integrations (MangoHud, GameMode)
    - Custom library path configuration
    - Launch non-Steam programs with speedhack from the UI

    Signals:
        generate_requested: Emitted when generate button is clicked
        library_path_changed: Emitted when library path changes (str)
        options_changed: Emitted when optional features change
        launch_external_requested: Emitted when non-Steam launch is requested
    """

    generate_requested = pyqtSignal()
    library_path_changed = pyqtSignal(str)
    options_changed = pyqtSignal(dict)
    launch_external_requested = pyqtSignal(str, bool, bool)

    # Default library path
    DEFAULT_LIBRARY_PATH = "/usr/lib/zblz/speedhack.so"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Steam and Non-Steam Launch")
        group_layout = QVBoxLayout(group)

        # Library path configuration
        path_layout = QHBoxLayout()

        path_label = QLabel("Speedhack Library:")
        path_layout.addWidget(path_label)

        self._path_input = QLineEdit(self.DEFAULT_LIBRARY_PATH)
        self._path_input.textChanged.connect(
            lambda text: self.library_path_changed.emit(text)
        )
        path_layout.addWidget(self._path_input)

        group_layout.addLayout(path_layout)

        # Optional integrations
        options_layout = QHBoxLayout()

        self._mangohud_check = QCheckBox("MangoHud")
        self._mangohud_check.setToolTip("Add MangoHud overlay for FPS/stats")
        self._mangohud_check.stateChanged.connect(self._on_options_changed)
        options_layout.addWidget(self._mangohud_check)

        self._gamemode_check = QCheckBox("GameMode")
        self._gamemode_check.setToolTip("Use Feral GameMode for performance")
        self._gamemode_check.stateChanged.connect(self._on_options_changed)
        options_layout.addWidget(self._gamemode_check)

        options_layout.addStretch()
        group_layout.addLayout(options_layout)

        # Steam command generation
        self._generate_btn = QPushButton("Generate Steam Launch Option")
        self._generate_btn.setObjectName("primary")
        self._generate_btn.clicked.connect(self.generate_requested.emit)
        group_layout.addWidget(self._generate_btn)

        output_label = QLabel("Generated Steam Command:")
        output_label.setObjectName("section-header")
        group_layout.addWidget(output_label)

        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setMaximumHeight(100)
        self._output_text.setPlaceholderText(
            "Click 'Generate Steam Launch Option' to create the command..."
        )
        group_layout.addWidget(self._output_text)

        copy_layout = QHBoxLayout()
        copy_layout.addStretch()

        self._copy_btn = QPushButton("Copy to Clipboard")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        copy_layout.addWidget(self._copy_btn)

        group_layout.addLayout(copy_layout)

        # Non-Steam launcher
        external_label = QLabel("Launch non-Steam app (command):")
        external_label.setObjectName("section-header")
        group_layout.addWidget(external_label)

        self._external_cmd_input = QLineEdit()
        self._external_cmd_input.setPlaceholderText(
            "Example: /home/user/Games/MyGame/game.sh --fullscreen"
        )
        self._external_cmd_input.returnPressed.connect(self._emit_external_launch)
        group_layout.addWidget(self._external_cmd_input)

        self._launch_external_btn = QPushButton("Launch Non-Steam with Speedhack")
        self._launch_external_btn.clicked.connect(self._emit_external_launch)
        group_layout.addWidget(self._launch_external_btn)

        instructions = QLabel(
            "Steam: Right-click game -> Properties -> Launch Options\n"
            "Non-Steam: write command above and click launch\n"
            "Steam compatibility: keeps existing LD_PRELOAD (overlay/online)"
        )
        instructions.setObjectName("subtitle")
        instructions.setWordWrap(True)
        group_layout.addWidget(instructions)

        layout.addWidget(group)

    def _on_options_changed(self):
        """Emit options changed signal with current state."""
        options = {
            "include_mangohud": self._mangohud_check.isChecked(),
            "include_gamemode": self._gamemode_check.isChecked(),
        }
        self.options_changed.emit(options)

    def _emit_external_launch(self):
        """Emit request to launch a non-Steam program with speedhack."""
        command = self._external_cmd_input.text().strip()
        self.launch_external_requested.emit(
            command,
            self._mangohud_check.isChecked(),
            self._gamemode_check.isChecked(),
        )

    def _copy_to_clipboard(self):
        """Copy the generated command to clipboard."""
        text = self._output_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

            # Visual feedback
            original_text = self._copy_btn.text()
            self._copy_btn.setText("Copied!")
            self._copy_btn.setEnabled(False)

            # Reset after delay
            QTimer.singleShot(1500, lambda: self._reset_copy_button(original_text))

    def _reset_copy_button(self, text: str):
        """Reset copy button to original state."""
        self._copy_btn.setText(text)
        self._copy_btn.setEnabled(True)

    def set_command(self, command: str):
        """Set the output command text."""
        self._output_text.setPlainText(command)
        self._copy_btn.setEnabled(bool(command))

    def get_command(self) -> str:
        """Get the current command text."""
        return self._output_text.toPlainText()

    def get_library_path(self) -> str:
        """Get the configured library path."""
        return self._path_input.text()

    def set_library_path(self, path: str):
        """Set the library path."""
        self._path_input.setText(path)

    def get_options(self) -> dict:
        """Get the current optional settings."""
        return {
            "include_mangohud": self._mangohud_check.isChecked(),
            "include_gamemode": self._gamemode_check.isChecked(),
        }

    def get_external_command(self) -> str:
        """Get non-Steam command input text."""
        return self._external_cmd_input.text().strip()

    def clear(self):
        """Clear the output."""
        self._output_text.clear()
        self._copy_btn.setEnabled(False)
