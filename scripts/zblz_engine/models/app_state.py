"""
ZBLZ Engine - Application State Model
Manages the core application state and data.

This model is designed to be extended for future features like:
- Memory scanning results
- Process attachment state
- Real-time speed control state
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from enum import Enum


class SpeedHackMode(Enum):
    """Modes for speed manipulation."""
    LAUNCH_OPTION = "launch_option"  # Generate Steam launch option
    REALTIME = "realtime"            # Future: Real-time injection


@dataclass
class ProcessInfo:
    """
    Represents a running process.
    Prepared for future process scanning/attachment features.
    """
    pid: int
    name: str
    cmdline: str = ""
    is_wine_process: bool = False
    is_proton_process: bool = False
    is_hooked: bool = False  # True if speedhack library is loaded
    
    def __str__(self) -> str:
        hooked = " [HOOKED]" if self.is_hooked else ""
        return f"[{self.pid}] {self.name}{hooked}"


@dataclass
class SpeedHackConfig:
    """Configuration for the speedhack feature."""
    speed_multiplier: float = 1.0
    library_path: str = "/usr/lib/zblz/speedhack.so"
    min_speed: float = 0.1
    max_speed: float = 5.0
    
    def clamp_speed(self, value: float) -> float:
        """Clamp speed value to valid range."""
        return max(self.min_speed, min(self.max_speed, value))


class AppState:
    """
    Central application state manager.
    
    Uses observer pattern to notify views of state changes.
    Extend this class to add new features (memory scanning, etc.)
    """
    
    def __init__(self):
        self._speed_config = SpeedHackConfig()
        self._processes: List[ProcessInfo] = []
        self._selected_process: Optional[ProcessInfo] = None
        self._mode = SpeedHackMode.LAUNCH_OPTION
        self._observers: List[Callable] = []
        
        # Future: Memory scanning state
        self._memory_scan_results: List = []
        
        # Future: Attachment state
        self._attached_pid: Optional[int] = None
    
    # ==================== Observer Pattern ====================
    
    def add_observer(self, callback: Callable) -> None:
        """Register a callback to be notified of state changes."""
        self._observers.append(callback)
    
    def remove_observer(self, callback: Callable) -> None:
        """Remove a registered observer."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, event: str) -> None:
        """Notify all observers of a state change."""
        for callback in self._observers:
            callback(event)
    
    # ==================== Speed Configuration ====================
    
    @property
    def speed_multiplier(self) -> float:
        return self._speed_config.speed_multiplier
    
    @speed_multiplier.setter
    def speed_multiplier(self, value: float) -> None:
        clamped = self._speed_config.clamp_speed(value)
        if clamped != self._speed_config.speed_multiplier:
            self._speed_config.speed_multiplier = clamped
            self._notify_observers("speed_changed")
    
    @property
    def speed_config(self) -> SpeedHackConfig:
        return self._speed_config
    
    @property
    def library_path(self) -> str:
        return self._speed_config.library_path
    
    @library_path.setter
    def library_path(self, value: str) -> None:
        self._speed_config.library_path = value
        self._notify_observers("library_path_changed")
    
    # ==================== Process Management ====================
    
    @property
    def processes(self) -> List[ProcessInfo]:
        return self._processes.copy()
    
    def set_processes(self, processes: List[ProcessInfo]) -> None:
        """Update the process list."""
        self._processes = processes
        self._notify_observers("processes_updated")
    
    @property
    def selected_process(self) -> Optional[ProcessInfo]:
        return self._selected_process
    
    @selected_process.setter
    def selected_process(self, process: Optional[ProcessInfo]) -> None:
        self._selected_process = process
        self._notify_observers("process_selected")
    
    # ==================== Mode Management ====================
    
    @property
    def mode(self) -> SpeedHackMode:
        return self._mode
    
    @mode.setter
    def mode(self, value: SpeedHackMode) -> None:
        self._mode = value
        self._notify_observers("mode_changed")
    
    # ==================== Future: Memory Scanning ====================
    
    def clear_memory_results(self) -> None:
        """Clear memory scan results. Prepared for future use."""
        self._memory_scan_results.clear()
        self._notify_observers("memory_cleared")
    
    # ==================== Future: Process Attachment ====================
    
    @property
    def is_attached(self) -> bool:
        """Check if currently attached to a process."""
        return self._attached_pid is not None
    
    def attach_to_process(self, pid: int) -> None:
        """Attach to a process. Prepared for future use."""
        self._attached_pid = pid
        self._notify_observers("process_attached")
    
    def detach(self) -> None:
        """Detach from current process. Prepared for future use."""
        self._attached_pid = None
        self._notify_observers("process_detached")
