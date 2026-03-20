"""
ZBLZ Engine - Command Output Widget
Displays generated launch commands with copy functionality.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QGroupBox, QCheckBox,
    QLineEdit, QApplication
)
from PyQt5.QtCore import pyqtSignal


class CommandOutputWidget(QWidget):
    """
    Widget for displaying and copying generated launch commands.
    
    Features:
    - Command output display
    - Copy to clipboard button
    - Optional integrations (MangoHud, GameMode)
    - Custom library path configuration
    
    Signals:
        generate_requested: Emitted when generate button is clicked
        library_path_changed: Emitted when library path changes (str)
        options_changed: Emitted when optional features change
    """
    
    generate_requested = pyqtSignal()
    library_path_changed = pyqtSignal(str)
    options_changed = pyqtSignal(dict)
    
    # Default library path
    DEFAULT_LIBRARY_PATH = "/usr/lib/zblz/speedhack.so"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Steam Launch Options")
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
        
        # Generate button
        self._generate_btn = QPushButton("Generate Steam Launch Option")
        self._generate_btn.setObjectName("primary")
        self._generate_btn.clicked.connect(self.generate_requested.emit)
        group_layout.addWidget(self._generate_btn)
        
        # Output area
        output_label = QLabel("Generated Command:")
        output_label.setObjectName("section-header")
        group_layout.addWidget(output_label)
        
        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setMaximumHeight(100)
        self._output_text.setPlaceholderText(
            "Click 'Generate Steam Launch Option' to create the command..."
        )
        group_layout.addWidget(self._output_text)
        
        # Copy button
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()
        
        self._copy_btn = QPushButton("Copy to Clipboard")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        copy_layout.addWidget(self._copy_btn)
        
        group_layout.addLayout(copy_layout)
        
        # Instructions
        instructions = QLabel(
            "Paste this command in Steam:\n"
            "Right-click game → Properties → General → Launch Options"
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
            from PyQt5.QtCore import QTimer
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
    
    def clear(self):
        """Clear the output."""
        self._output_text.clear()
        self._copy_btn.setEnabled(False)
