"""
ZBLZ Engine - Main Controller
Handles business logic and coordinates between the model and view.

This controller is designed to be extended with additional sub-controllers
for features like memory scanning, process attachment, etc.
"""

import os
from typing import Optional, TYPE_CHECKING
from models.app_state import AppState, ProcessInfo, SpeedHackMode
from services.process_scanner import ProcessScanner
from services.speed_controller import SpeedController

if TYPE_CHECKING:
    from views.main_window import MainWindow


class MainController:
    """
    Main application controller.
    
    Responsibilities:
    - Handle user actions from the view
    - Update the model based on user input
    - Generate output (launch commands, etc.)
    - Control speed in real-time for attached processes
    """
    
    # main_controller.py (Fragmentos a actualizar)

    # Añade esto en el __init__ de MainController para recordar la preferencia
    # controllers/main_controller.py

    def __init__(self, model: AppState):
        self._model = model
        self._view: Optional["MainWindow"] = None
        
        # Initialize services
        self._process_scanner = ProcessScanner()
        self._speed_controller = SpeedController()
        
        # --- CAMBIA ESTO A FALSE TEMPORALMENTE ---
        # Así forzamos a que liste todo al arrancar
        self._show_games_only = False 
        
        # Set default library path
        self._set_default_library_path()
        
        # Register as observer to react to model changes
        self._model.add_observer(self._on_model_changed)

    # Actualiza el método refresh_processes
    # controllers/main_controller.py

   # Actualiza el método en controllers/main_controller.py

    def refresh_processes(self, games_only: bool = False) -> None: # Cambiado a False para testear
        """Refresca la lista y notifica a la UI."""
        try:
            if games_only:
                processes = self._process_scanner.scan_games_only()
            else:
                # Obtenemos todos los procesos que NO sean del kernel
                processes = self._process_scanner.scan_all(include_system=False)
            
            # Verificación de inyección (speedhack)
            for process in processes:
                process.is_hooked = self._speed_controller.is_process_hooked(process.pid)
            
            # Enviamos al modelo. Esto disparará 'processes_updated'
            self._model.set_processes(processes)
            
            if self._view:
                self._view.show_status(f"Mostrando {len(processes)} procesos.")
                
        except Exception as e:
            if self._view:
                self._view.show_error(f"Fallo en el motor de escaneo: {str(e)}")
    
    def _set_default_library_path(self) -> None:
        """Set the default speedhack library path."""
        possible_paths = [
            os.path.expanduser("~/.local/lib/zblz/libspeedhack.so"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib", "libspeedhack.so"),
            "/usr/local/lib/zblz/libspeedhack.so",
            "/usr/lib/zblz/libspeedhack.so",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self._model.library_path = path
                return
        
        self._model.library_path = os.path.expanduser("~/.local/lib/zblz/libspeedhack.so")
    
    def set_view(self, view: "MainWindow") -> None:
        """Connect the view to this controller."""
        self._view = view
    
    @property
    def model(self) -> AppState:
        """Access the application state model."""
        return self._model
    
    # ==================== Event Handlers ====================
    
    def _on_model_changed(self, event: str) -> None:
        """React to model state changes."""
        if self._view is None:
            return
        
        if event == "speed_changed":
            self._view.update_speed_display(self._model.speed_multiplier)
            # If attached to a process, update speed in real-time
            if self._model.is_attached:
                self._speed_controller.set_speed(self._model.speed_multiplier)
        elif event == "processes_updated":
            self._view.update_process_list(self._model.processes)
        elif event == "process_attached":
            self._view.show_status(f"Attached to PID {self._model._attached_pid}")
        elif event == "process_detached":
            self._view.show_status("Detached from process")
    
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
        
        Format: LD_PRELOAD=/path/to/speedhack.so ZBLZ_PID=$$ %command%
        """
        library_path = self._model.library_path
        speed = self._model.speed_multiplier
        
        if not library_path:
            return "# Error: Library path not set"
        
        # ZBLZ_PID=$$ passes the shell's PID to the library
        command = f'LD_PRELOAD="{library_path}" SPEED={speed:.2f} ZBLZ_PID=$$ %command%'
        
        return command
    
    def generate_launch_command_with_options(
        self,
        include_mangohud: bool = False,
        include_gamemode: bool = False,
        custom_env: dict = None
    ) -> str:
        """Generate launch command with additional options."""
        parts = []
        
        if include_gamemode:
            parts.append("gamemoderun")
        
        if include_mangohud:
            parts.append("mangohud")
        
        if custom_env:
            for key, value in custom_env.items():
                parts.append(f'{key}="{value}"')
        
        parts.append(f'LD_PRELOAD="{self._model.library_path}"')
        parts.append(f'SPEED={self._model.speed_multiplier:.2f}')
        parts.append('ZBLZ_PID=$$')
        parts.append("%command%")
        
        return " ".join(parts)
    
    # ==================== Process Management ====================
    
    def refresh_processes(self, games_only: bool = True) -> None:
        """Refresh the process list by scanning /proc."""
        try:
            if games_only:
                processes = self._process_scanner.scan_games_only()
            else:
                processes = self._process_scanner.scan_all(include_system=False)
            
            # Mark processes that have speedhack loaded
            for process in processes:
                process.is_hooked = self._speed_controller.is_process_hooked(process.pid)
            
            self._model.set_processes(processes)
            
            if self._view:
                count = len(processes)
                hooked_count = sum(1 for p in processes if getattr(p, 'is_hooked', False))
                if count == 0:
                    self._view.show_status("No game processes found. Start a game first.")
                elif hooked_count > 0:
                    self._view.show_status(f"Found {count} process(es), {hooked_count} with speedhack")
                else:
                    self._view.show_status(f"Found {count} process(es)")
        
        except Exception as e:
            if self._view:
                self._view.show_error(f"Error scanning processes: {str(e)}")
    
    def select_process(self, process: ProcessInfo) -> None:
        """Select a process from the list."""
        self._model.selected_process = process
    
    def attach_to_selected(self) -> None:
        """Attach to the currently selected process for real-time control."""
        if self._model.selected_process is None:
            if self._view:
                self._view.show_error("No process selected")
            return
        
        pid = self._model.selected_process.pid
        
        # Check if process has speedhack loaded
        if not self._speed_controller.is_process_hooked(pid):
            if self._view:
                self._view.show_error(
                    f"Process {pid} doesn't have speedhack loaded.\n"
                    "Start the game with the Steam launch command first."
                )
            return
        
        # Attach to process
        if self._speed_controller.attach(pid):
            self._model.attach_to_process(pid)
            self._model.mode = SpeedHackMode.REALTIME
            
            # Set current speed
            self._speed_controller.set_speed(self._model.speed_multiplier)
            
            if self._view:
                self._view.set_attached_state(True, pid)
                self._view.show_status(f"Attached to PID {pid} - Real-time control enabled!")
        else:
            if self._view:
                self._view.show_error(f"Failed to attach to process {pid}")
    
    def detach_from_process(self) -> None:
        """Detach from current process."""
        self._speed_controller.detach()
        self._model.detach()
        self._model.mode = SpeedHackMode.LAUNCH_OPTION
        
        if self._view:
            self._view.set_attached_state(False)
            self._view.show_status("Detached from process")
    
    def is_attached(self) -> bool:
        """Check if attached to a process."""
        return self._model.is_attached
