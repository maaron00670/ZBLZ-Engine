"""
ZBLZ Engine - Main Controller
Handles business logic and coordinates between the model and view.

This controller is designed to be extended with additional sub-controllers
for features like memory scanning, process attachment, etc.
"""

import os
import shlex
import subprocess
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

    def __init__(self, model: AppState):
        self._model = model
        self._view: Optional["MainWindow"] = None

        # Initialize services
        self._process_scanner = ProcessScanner()
        self._speed_controller = SpeedController()

        # Set default library path
        self._set_default_library_path()

        # Register as observer to react to model changes
        self._model.add_observer(self._on_model_changed)

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
                applied = self._speed_controller.set_speed(self._model.speed_multiplier)
                if not applied:
                    self._view.show_error("Couldn't apply speed in real-time to attached process")
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

        # ZBLZ_PID=$$ passes a stable control PID to the library
        command = f'LD_PRELOAD="{library_path}${{LD_PRELOAD:+:$LD_PRELOAD}}" SPEED={speed:.2f} ZBLZ_PID=$$ %command%'

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

        parts.append(f'LD_PRELOAD="{self._model.library_path}${{LD_PRELOAD:+:$LD_PRELOAD}}"')
        parts.append(f'SPEED={self._model.speed_multiplier:.2f}')
        parts.append('ZBLZ_PID=$$')
        parts.append("%command%")

        return " ".join(parts)

    def launch_external_program(
        self,
        command: str,
        include_mangohud: bool = False,
        include_gamemode: bool = False,
    ) -> tuple[bool, str]:
        """
        Launch a non-Steam program with speedhack preloaded.

        Returns:
            (success, user_message)
        """
        target_command = command.strip()
        if not target_command:
            return False, "Write a command first (path/to/program [args])"

        library_path = self._model.library_path.strip()
        if not library_path:
            return False, "Speedhack library path is empty"

        if not os.path.exists(library_path):
            return False, f"Library not found: {library_path}"

        try:
            target_args = shlex.split(target_command)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"

        if not target_args:
            return False, "Invalid command"

        launch_args = []
        if include_gamemode:
            launch_args.append("gamemoderun")
        if include_mangohud:
            launch_args.append("mangohud")
        launch_args.extend(target_args)

        env = os.environ.copy()
        existing_preload = env.get("LD_PRELOAD", "").strip()
        if existing_preload:
            env["LD_PRELOAD"] = f"{library_path}:{existing_preload}"
        else:
            env["LD_PRELOAD"] = library_path

        # Keep per-process config for non-Steam launches
        env.pop("ZBLZ_PID", None)
        env["SPEED"] = f"{self._model.speed_multiplier:.2f}"

        try:
            process = subprocess.Popen(
                launch_args,
                env=env,
                start_new_session=True,
            )
        except FileNotFoundError:
            return False, f"Command not found: {launch_args[0]}"
        except Exception as e:
            return False, f"Launch failed: {e}"

        return (
            True,
            f"Launched PID {process.pid} with speedhack. Refresh and attach for real-time control.",
        )

    # ==================== Process Management ====================

    def refresh_processes(self, games_only: bool = True) -> None:
        """Refresh the process list by scanning /proc."""
        try:
            if games_only:
                processes = self._process_scanner.scan_games_only()
            else:
                # Show ALL user processes when "Games only" is unchecked
                processes = self._process_scanner.scan_user_processes()

            # Mark processes that have speedhack loaded
            for process in processes:
                process.is_hooked = self._speed_controller.is_process_hooked(process.pid)

            self._model.set_processes(processes)

            if self._view:
                count = len(processes)
                hooked_count = sum(1 for p in processes if getattr(p, 'is_hooked', False))
                if count == 0:
                    if games_only:
                        self._view.show_status("No game processes found. Start a game first.")
                    else:
                        self._view.show_status("No user processes found.")
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
                    "Start the target app with LD_PRELOAD first (Steam launch options or terminal)."
                )
            return

        # Attach to process
        if self._speed_controller.attach(pid):
            control_pid = self._speed_controller.attached_pid

            self._model.attach_to_process(pid)
            self._model.mode = SpeedHackMode.REALTIME

            # Set current speed immediately on attach
            applied = self._speed_controller.set_speed(self._model.speed_multiplier)

            if self._view:
                self._view.set_attached_state(True, pid)

                if control_pid is not None and control_pid != pid:
                    self._view.show_status(
                        f"Attached to PID {pid} (control PID {control_pid}) - Real-time control enabled!"
                    )
                else:
                    self._view.show_status(f"Attached to PID {pid} - Real-time control enabled!")

                if not applied:
                    self._view.show_error("Attached, but initial speed write failed")
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
