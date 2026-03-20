"""
ZBLZ Engine - Speed Control Widget
Reusable widget for controlling game speed.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QLineEdit, QPushButton, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal


class SpeedControlWidget(QWidget):
    """
    Widget for controlling the speed multiplier.
    
    Features:
    - Slider for quick adjustment (0.1x to 5.0x)
    - Text input for precise values
    - Preset buttons for common speeds
    
    Signals:
        speed_changed: Emitted when speed value changes (float)
    """
    
    speed_changed = pyqtSignal(float)
    
    # Preset speed values
    PRESETS = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_speed = 1.0
        self._min_speed = 0.1
        self._max_speed = 5.0
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Group box for visual grouping
        group = QGroupBox("Speed Control")
        group_layout = QVBoxLayout(group)
        
        # Speed display row
        display_layout = QHBoxLayout()
        
        self._speed_label = QLabel("Speed Multiplier:")
        display_layout.addWidget(self._speed_label)
        
        self._speed_input = QLineEdit("1.00")
        self._speed_input.setMaximumWidth(80)
        self._speed_input.setAlignment(Qt.AlignCenter)
        self._speed_input.returnPressed.connect(self._on_input_changed)
        display_layout.addWidget(self._speed_input)
        
        self._speed_suffix = QLabel("x")
        display_layout.addWidget(self._speed_suffix)
        
        display_layout.addStretch()
        group_layout.addLayout(display_layout)
        
        # Slider row
        slider_layout = QHBoxLayout()
        
        self._min_label = QLabel(f"{self._min_speed}x")
        self._min_label.setObjectName("subtitle")
        slider_layout.addWidget(self._min_label)
        
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setMinimum(int(self._min_speed * 100))
        self._slider.setMaximum(int(self._max_speed * 100))
        self._slider.setValue(100)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.setTickInterval(50)
        self._slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self._slider)
        
        self._max_label = QLabel(f"{self._max_speed}x")
        self._max_label.setObjectName("subtitle")
        slider_layout.addWidget(self._max_label)
        
        group_layout.addLayout(slider_layout)
        
        # Preset buttons row
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:")
        preset_label.setObjectName("subtitle")
        preset_layout.addWidget(preset_label)
        
        for speed in self.PRESETS:
            btn = QPushButton(f"{speed}x")
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, s=speed: self.set_speed(s))
            preset_layout.addWidget(btn)
        
        preset_layout.addStretch()
        group_layout.addLayout(preset_layout)
        
        layout.addWidget(group)
    
    def _on_slider_changed(self, value: int):
        """Handle slider value changes."""
        speed = value / 100.0
        self._update_speed(speed, update_slider=False)
    
    def _on_input_changed(self):
        """Handle text input changes."""
        try:
            speed = float(self._speed_input.text())
            speed = max(self._min_speed, min(self._max_speed, speed))
            self._update_speed(speed, update_input=False)
        except ValueError:
            # Reset to current value on invalid input
            self._speed_input.setText(f"{self._current_speed:.2f}")
    
    def _update_speed(self, speed: float, update_slider=True, update_input=True):
        """Update all UI elements and emit signal."""
        self._current_speed = speed
        
        if update_slider:
            self._slider.blockSignals(True)
            self._slider.setValue(int(speed * 100))
            self._slider.blockSignals(False)
        
        if update_input:
            self._speed_input.setText(f"{speed:.2f}")
        
        self.speed_changed.emit(speed)
    
    def set_speed(self, speed: float):
        """Set the speed value programmatically."""
        speed = max(self._min_speed, min(self._max_speed, speed))
        self._update_speed(speed)
    
    def get_speed(self) -> float:
        """Get the current speed value."""
        return self._current_speed
    
    def set_range(self, min_speed: float, max_speed: float):
        """Update the allowed speed range."""
        self._min_speed = min_speed
        self._max_speed = max_speed
        
        self._slider.setMinimum(int(min_speed * 100))
        self._slider.setMaximum(int(max_speed * 100))
        
        self._min_label.setText(f"{min_speed}x")
        self._max_label.setText(f"{max_speed}x")
        
        # Clamp current value to new range
        self.set_speed(self._current_speed)
