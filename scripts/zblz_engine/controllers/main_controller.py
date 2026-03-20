"""
ZBLZ Engine - Main Controller
Handles business logic and coordinates between the model and view.

This controller is designed to be extended with additional sub-controllers
for features like memory scanning, process attachment, etc.
"""

from typing import Optional, TYPE_CHECKING
from models.app_state import AppState, ProcessInfo

if TYPE_CHECKING:
    from views.main_window import MainWindow


class MainController:
    """
    Main application controller.
    
    Responsibilities:
    - Handle user actions from the view
    - Update the model based on user input
    - Generate output (launch commands, etc.)
    - Coordinate with backend services (future)
    
    To extend:
    - Add sub-controllers for specific features
    - Register them in __init__
    - Delegate feature-specific logic to sub-controllers
    """
    
    def __init__(self, model: AppState):
        self._model = model
        self._view: Optional["MainWindow"] = None
        
        # Register as observer to react to model changes
        self._model.add_observer(self._on_model_changed)
        
        # Future: Initialize sub-controllers here
        # self._memory_controller = MemoryController(model)
        # self._process_controller = ProcessController(model)
    
    def set_view(self, view: "MainWindow") -> None:
        """Connect the view to this controller."""
        self._view = view
    
    @property
    def model(self) -> AppState:
        """Access the application state model."""
        return self._model
    
    # ==================== Event Handlers ====================
    
    def _on_model_changed(self, event: str) -> None:
        """
        React to model state changes.
        Update the view or trigger side effects as needed.
        """
        if self._view is None:
            return
        
        if event == "speed_changed":
            self._view.update_speed_display(self._model.speed_multiplier)
        elif event == "processes_updated":
            self._view.update_process_list(self._model.processes)
        elif event == "process_attached":
            self._view.show_status("Process attached successfully")
        elif event == "process_detached":
            self._view.show_status("Process detached")
    
    # ==================== Speed Control ====================
    
    def set_speed(self, value: float) -> None:
        """Update the speed multiplier."""
        self._model.speed_multiplier = value
    
    def get_speed(self) -> float:
        """Get the current speed multiplier."""
        return self._model.speed_multiplier
    
    def set_library_path(self, path: str) -> None:
        """Update the speedhack library path."""
        self._model.library_path = path
    
    # ==================== Launch Command Generation ====================
    
    def generate_launch_command(self) -> str:
        """
        Generate the Steam launch option command.
        
        Format: LD_PRELOAD=/path/to/speedhack.so SPEED=X.X %command%
        
        This command should be added to Steam game properties:
        Right-click game -> Properties -> Launch Options
        """
        library_path = self._model.library_path
        speed = self._model.speed_multiplier
        
        # Validate library path
        if not library_path:
            return "# Error: Library path not set"
        
        # Generate the command
        command = f'LD_PRELOAD="{library_path}" SPEED={speed:.2f} %command%'
        
        return command
    
    def generate_launch_command_with_options(
        self,
        include_mangohud: bool = False,
        include_gamemode: bool = False,
        custom_env: dict = None
    ) -> str:
        """
        Generate launch command with additional options.
        
        Args:
            include_mangohud: Add MangoHud overlay
            include_gamemode: Add GameMode for performance
            custom_env: Additional environment variables
        
        Returns:
            Complete launch command string
        """
        parts = []
        
        # Add GameMode if requested
        if include_gamemode:
            parts.append("gamemoderun")
        
        # Add MangoHud if requested
        if include_mangohud:
            parts.append("mangohud")
        
        # Add custom environment variables
        if custom_env:
            for key, value in custom_env.items():
                parts.append(f'{key}="{value}"')
        
        # Add speedhack
        parts.append(f'LD_PRELOAD="{self._model.library_path}"')
        parts.append(f'SPEED={self._model.speed_multiplier:.2f}')
        
        # Add the command placeholder
        parts.append("%command%")
        
        return " ".join(parts)
    
    # ==================== Process Management (Future) ====================
    
    def refresh_processes(self) -> None:
        """
        Refresh the process list.
        
        Future implementation will scan /proc for running processes
        and identify Wine/Proton games.
        """
        # Placeholder for future implementation
        # This would call a backend service to scan processes
        
        # Example of what the backend would return:
        demo_processes = [
            ProcessInfo(pid=1234, name="wine-preloader", is_wine_process=True),
            ProcessInfo(pid=5678, name="proton", is_proton_process=True),
        ]
        
        # For now, just show placeholder
        self._model.set_processes(demo_processes)
        
        if self._view:
            self._view.show_status("Process scanning not yet implemented")
    
    def select_process(self, process: ProcessInfo) -> None:
        """Select a process from the list."""
        self._model.selected_process = process
    
    def attach_to_selected(self) -> None:
        """
        Attach to the currently selected process.
        Future: Will enable real-time speed control.
        """
        if self._model.selected_process is None:
            if self._view:
                self._view.show_status("No process selected")
            return
        
        # Future: Implement actual attachment logic
        if self._view:
            self._view.show_status("Process attachment not yet implemented")
    
    # ==================== Memory Scanning (Future) ====================
    
    def scan_memory(self, value: int, scan_type: str = "exact") -> None:
        """
        Scan memory for a value.
        Future: Will implement memory scanning like Cheat Engine.
        
        Args:
            value: The value to search for
            scan_type: Type of scan (exact, greater, less, between, etc.)
        """
        # Placeholder for future implementation
        if self._view:
            self._view.show_status("Memory scanning not yet implemented")
    
    def next_scan(self, value: int) -> None:
        """
        Perform a next scan on existing results.
        Future: Will filter previous scan results.
        """
        pass
    
    def write_memory(self, address: int, value: int) -> None:
        """
        Write a value to a memory address.
        Future: Will modify game memory.
        """
        pass
