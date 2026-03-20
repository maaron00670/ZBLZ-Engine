"""
ZBLZ Engine - Real-time Speed Controller
Communicates with the speedhack library via config file.
"""

import os
from pathlib import Path
from typing import Optional


class SpeedController:
    """
    Controls game speed in real-time by writing to config files
    that the injected speedhack library reads.
    """
    
    def __init__(self):
        self._config_dir = Path.home() / ".config" / "zblz"
        self._attached_pid: Optional[int] = None
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_config_path(self, pid: int) -> Path:
        """Get config file path for a specific PID."""
        return self._config_dir / f"speed_{pid}.conf"
    
    def attach(self, pid: int) -> bool:
        """
        Attach to a process for real-time speed control.
        
        Args:
            pid: Process ID to attach to
            
        Returns:
            True if config file exists (process is using speedhack)
        """
        config_path = self._get_config_path(pid)
        
        # Check if process has speedhack loaded (config file exists)
        if config_path.exists():
            self._attached_pid = pid
            return True
        
        # Config doesn't exist - process might not have speedhack loaded
        # Try to create it anyway (in case process checks for it)
        try:
            with open(config_path, 'w') as f:
                f.write("1.0\n")
            self._attached_pid = pid
            return True
        except Exception:
            return False
    
    def detach(self) -> None:
        """Detach from current process."""
        self._attached_pid = None
    
    # services/speed_controller.py
# services/speed_controller.py

    def set_speed(self, speed: float) -> bool:
        if not self._attached_pid:
            return False
            
        config_path = self._get_config_path(self._attached_pid)
        try:
            # Aseguramos que el directorio ~/.config/zblz existe
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            # Escribimos con 'with' para cerrar el archivo rápido
            with open(config_path, "w") as f:
                f.write(f"{speed:.2f}")
                f.flush()
                os.fsync(f.fileno()) # <--- CRÍTICO: Fuerza al kernel a escribir en disco
            return True
        except Exception as e:
            print(f"Fallo al escribir speed conf: {e}")
            return False
    
    def is_process_hooked(self, pid: int) -> bool:
        """
        Check if a process has the speedhack library loaded.
        
        Args:
            pid: Process ID to check
            
        Returns:
            True if process appears to have speedhack loaded
        """
        # Check if config file exists
        config_path = self._get_config_path(pid)
        if config_path.exists():
            return True
        
        # Check if process has libspeedhack.so loaded
        try:
            maps_path = f"/proc/{pid}/maps"
            with open(maps_path, 'r') as f:
                for line in f:
                    if 'libspeedhack.so' in line:
                        return True
        except Exception:
            pass
        
        return False
    
    def list_hooked_processes(self) -> list[int]:
        """
        Find all processes that have speedhack loaded.
        
        Returns:
            List of PIDs with speedhack active
        """
        hooked = []
        
        # Check for config files
        for config_file in self._config_dir.glob("speed_*.conf"):
            try:
                pid = int(config_file.stem.split('_')[1])
                # Verify process still exists
                if os.path.exists(f"/proc/{pid}"):
                    hooked.append(pid)
                else:
                    # Clean up stale config file
                    config_file.unlink()
            except (ValueError, IndexError):
                pass
        
        return hooked
    
    @property
    def attached_pid(self) -> Optional[int]:
        """Get currently attached PID."""
        return self._attached_pid
    
    @property
    def is_attached(self) -> bool:
        """Check if currently attached to a process."""
        return self._attached_pid is not None
