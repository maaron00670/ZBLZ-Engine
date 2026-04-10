"""
ZBLZ Engine - Main Window
Primary application window containing all UI components.
"""

from typing import List, TYPE_CHECKING
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStatusBar, QTabWidget, QSplitter,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from views.styles import DARK_THEME
from views.widgets import SpeedControlWidget, ProcessListWidget, CommandOutputWidget, HotkeysWidget

if TYPE_CHECKING:
    from controllers.main_controller import MainController
    from models.app_state import ProcessInfo


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Layout:
    - Header with title and version
    - Tab widget with:
        - Speedhack tab (current functionality)
        - Memory tab (future)
        - Settings tab (future)
    - Status bar for messages
    
    To extend:
    - Add new tabs for features
    - Create corresponding widgets
    - Connect to controller methods
    """
    
    WINDOW_TITLE = "ZBLZ Engine"
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 600
    
    def __init__(self, controller: "MainController"):
        super().__init__()
        self._controller = controller
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_window(self):
        """Configure the main window properties."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT)
        self.setStyleSheet(DARK_THEME)
    
    def _setup_ui(self):
        """Initialize the UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tab widget for different features
        self._tabs = QTabWidget()
        
        # Speedhack tab
        speedhack_tab = self._create_speedhack_tab()
        self._tabs.addTab(speedhack_tab, "Speedhack")
        
        # Memory tab (placeholder for future)
        memory_tab = self._create_memory_tab()
        self._tabs.addTab(memory_tab, "Memory Scanner")
        
        # Settings tab (placeholder for future)
        settings_tab = self._create_settings_tab()
        self._tabs.addTab(settings_tab, "Settings")
        
        main_layout.addWidget(self._tabs)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")
    
    def _create_header(self) -> QWidget:
        """Create the application header."""
        header = QFrame()
        header.setFrameStyle(QFrame.NoFrame)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel(self.WINDOW_TITLE)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Linux Game Speed Manipulation Tool")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        # Version
        version = QLabel("v0.1.0")
        version.setObjectName("subtitle")
        layout.addWidget(version)
        
        return header
    
    def _create_speedhack_tab(self) -> QWidget:
        """Create the speedhack tab content."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(16)
        
        # Left panel - Process list (for future use)
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self._process_list = ProcessListWidget()
        left_layout.addWidget(self._process_list)
        
        layout.addWidget(left_panel)
        
        # Right panel - Speed control and output
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Speed control widget
        self._speed_control = SpeedControlWidget()
        right_layout.addWidget(self._speed_control)

        # Hotkeys widget
        self._hotkeys = HotkeysWidget(self._controller.hotkey_manager)
        right_layout.addWidget(self._hotkeys)

        # Command output widget
        self._command_output = CommandOutputWidget()
        right_layout.addWidget(self._command_output)
        
        right_layout.addStretch()
        
        layout.addWidget(right_panel)
        
        return tab
    
    def _create_memory_tab(self) -> QWidget:
        """Create the memory scanner tab (placeholder)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Placeholder content
        placeholder = QLabel(
            "Memory Scanner\n\n"
            "This feature is planned for future development.\n\n"
            "Planned features:\n"
            "• Value scanning (exact, range, unknown)\n"
            "• Memory editing\n"
            "• Pointer scanning\n"
            "• Save/load scan results"
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setObjectName("subtitle")
        layout.addWidget(placeholder)
        
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """Create the settings tab (placeholder)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Placeholder content
        placeholder = QLabel(
            "Settings\n\n"
            "Configuration options coming soon.\n\n"
            "Planned settings:\n"
            "• Default library path\n"
            "• UI theme selection\n"
            "• Hotkey configuration\n"
            "• Process scan filters"
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setObjectName("subtitle")
        layout.addWidget(placeholder)
        
        return tab
    
    def _connect_signals(self):
        """Connect widget signals to controller methods."""
        # Speed control
        self._speed_control.speed_changed.connect(
            self._controller.set_speed
        )

        # Hotkeys
        self._hotkeys.increase_requested.connect(self._controller.increase_speed)
        self._hotkeys.reset_requested.connect(self._controller.reset_speed)
        self._hotkeys.decrease_requested.connect(self._controller.decrease_speed)

        # Process list
        self._process_list.refresh_requested.connect(
            lambda games_only: self._controller.refresh_processes(games_only)
        )
        self._process_list.process_selected.connect(
            self._controller.select_process
        )
        self._process_list.attach_requested.connect(
            self._controller.attach_to_selected
        )
        self._process_list.detach_requested.connect(
            self._controller.detach_from_process
        )
        
        # Command output
        self._command_output.generate_requested.connect(
            self._on_generate_command
        )
        self._command_output.library_path_changed.connect(
            self._controller.set_library_path
        )
        self._command_output.launch_external_requested.connect(
            self._on_launch_external_program
        )
    
    def _on_generate_command(self):
        """Handle generate command button click."""
        options = self._command_output.get_options()
        
        # Generate command with options
        command = self._controller.generate_launch_command_with_options(
            include_mangohud=options.get("include_mangohud", False),
            include_gamemode=options.get("include_gamemode", False)
        )
        
        self._command_output.set_command(command)
        self.show_status("Launch command generated")

    def _on_launch_external_program(self, command: str, include_mangohud: bool, include_gamemode: bool):
        """Handle launch request for non-Steam program."""
        success, message = self._controller.launch_external_program(
            command,
            include_mangohud=include_mangohud,
            include_gamemode=include_gamemode
        )

        if success:
            self.show_status(message, 8000)
            # Show all user processes so the launched app is easy to find
            self._controller.refresh_processes(games_only=False)
        else:
            self.show_error(message)

    # ==================== Public Methods for Controller ====================
    
    def update_speed_display(self, speed: float):
        """Update the speed display (called by controller)."""
        self._speed_control.set_speed(speed)
    
    def update_process_list(self, processes: List["ProcessInfo"]):
        """Update the process list (called by controller)."""
        self._process_list.set_processes(processes)
    
    def show_status(self, message: str, timeout: int = 5000):
        """Show a message in the status bar."""
        self._status_bar.showMessage(message, timeout)
    
    def show_error(self, message: str):
        """Show an error message."""
        self._status_bar.showMessage(f"Error: {message}", 10000)
    
    def set_attached_state(self, is_attached: bool, pid: int = None):
        """Update UI to reflect process attachment state."""
        self._process_list.set_attached(is_attached, pid)
