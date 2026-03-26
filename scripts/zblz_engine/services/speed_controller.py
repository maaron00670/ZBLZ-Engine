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
        # PID used by libspeedhack to read/write config (may differ from game PID)
        self._attached_pid: Optional[int] = None
        # PID selected in the UI
        self._attached_process_pid: Optional[int] = None
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _get_config_path(self, pid: int) -> Path:
        """Get config file path for a specific PID."""
        return self._config_dir / f"speed_{pid}.conf"

    def _resolve_control_pid(self, pid: int) -> int:
        """
        Resolve the config PID used by libspeedhack for a process.

        If the target process was launched with ZBLZ_PID, libspeedhack uses that
        value for ~/.config/zblz/speed_<PID>.conf instead of its own getpid().
        """
        environ_path = Path(f"/proc/{pid}/environ")
        try:
            data = environ_path.read_bytes()
            for entry in data.split(b"\x00"):
                if not entry or b"=" not in entry:
                    continue
                key, value = entry.split(b"=", 1)
                if key == b"ZBLZ_PID":
                    try:
                        control_pid = int(value.decode("utf-8", errors="ignore"))
                        if control_pid > 0:
                            return control_pid
                    except ValueError:
                        pass
        except Exception:
            pass

        return pid

    def attach(self, pid: int) -> bool:
        """
        Attach to a process for real-time speed control.

        Args:
            pid: Process ID selected in UI

        Returns:
            True if configuration target is available or writable
        """
        control_pid = self._resolve_control_pid(pid)
        config_path = self._get_config_path(control_pid)

        # Check if process has speedhack loaded (config file exists)
        if config_path.exists():
            self._attached_pid = control_pid
            self._attached_process_pid = pid
            return True

        # Config doesn't exist - process might not have speedhack loaded
        # Try to create it anyway (in case process checks for it)
        try:
            with open(config_path, 'w') as f:
                f.write("1.0\n")
            self._attached_pid = control_pid
            self._attached_process_pid = pid
            return True
        except Exception:
            return False

    def detach(self) -> None:
        """Detach from current process."""
        self._attached_pid = None
        self._attached_process_pid = None

    def set_speed(self, speed: float, pid: Optional[int] = None) -> bool:
        """
        Set speed for attached or specified process.

        Args:
            speed: Speed multiplier (0.1 to 10.0)
            pid: Optional process PID from list; resolved to control PID

        Returns:
            True if speed was written successfully
        """
        target_pid = self._resolve_control_pid(pid) if pid is not None else self._attached_pid
        if target_pid is None:
            return False

        # Clamp speed to valid range
        speed = max(0.01, min(100.0, speed))

        config_path = self._get_config_path(target_pid)

        try:
            with open(config_path, 'w') as f:
                f.write(f"{speed:.4f}\n")
            return True
        except Exception as e:
            print(f"[ZBLZ] Error writing speed config: {e}")
            return False

    def get_speed(self, pid: Optional[int] = None) -> Optional[float]:
        """
        Get current speed for attached or specified process.

        Args:
            pid: Optional process PID from list; resolved to control PID

        Returns:
            Current speed or None if not found
        """
        target_pid = self._resolve_control_pid(pid) if pid is not None else self._attached_pid
        if target_pid is None:
            return None

        config_path = self._get_config_path(target_pid)

        try:
            with open(config_path, 'r') as f:
                return float(f.read().strip())
        except Exception:
            return None

    def is_process_hooked(self, pid: int) -> bool:
        """
        Check if a process has the speedhack library loaded.

        Args:
            pid: Process ID to check

        Returns:
            True if process appears to have speedhack loaded
        """
        control_pid = self._resolve_control_pid(pid)

        # Check if config file exists for effective control PID
        config_path = self._get_config_path(control_pid)
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
        """Get currently attached control PID (config file PID)."""
        return self._attached_pid

    @property
    def attached_process_pid(self) -> Optional[int]:
        """Get currently attached selected process PID."""
        return self._attached_process_pid

    @property
    def is_attached(self) -> bool:
        """Check if currently attached to a process."""
        return self._attached_pid is not None
