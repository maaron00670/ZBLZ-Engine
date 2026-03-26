"""
ZBLZ Engine - Process Scanner
Scans running processes from /proc filesystem.
"""

import os
from typing import List, Optional

from models.app_state import ProcessInfo


class ProcessScanner:
    """
    Scans running processes on Linux using /proc.

    Supports two primary modes:
    - Games only (Wine/Proton/Steam heuristics)
    - All user processes (non-system)
    """

    WINE_INDICATORS = [
        "wine", "wine64", "wine-preloader", "wine64-preloader",
        "wineserver", "winedevice.exe", "services.exe"
    ]

    PROTON_INDICATORS = [
        "proton", "pressure-vessel", "steam-runtime"
    ]

    SYSTEM_PROCESSES = {
        "systemd", "kthreadd", "kworker", "ksoftirqd", "migration",
        "rcu_sched", "watchdog", "kdevtmpfs", "netns", "khungtaskd",
        "oom_reaper", "writeback", "kcompactd", "ksmd", "khugepaged",
        "crypto", "kintegrityd", "kblockd", "devfreq", "loop", "md",
        "edac-poller", "kswapd", "ecryptfs", "kthrotld", "irq", "acpi",
        "scsi", "nvme", "mpt", "ata", "kdmflush", "bioset", "dbus",
        "polkit", "rtkit", "accounts", "colord", "udisks", "upowerd"
    }

    def __init__(self):
        self._cache: List[ProcessInfo] = []
        self._current_uid = os.getuid()

    def scan_all(self, include_system: bool = True) -> List[ProcessInfo]:
        """
        Scan all readable processes from /proc.

        Args:
            include_system: Include likely system/kernel processes

        Returns:
            Sorted list of process info objects
        """
        processes: List[ProcessInfo] = []

        try:
            for pid_dir in os.listdir('/proc'):
                if not pid_dir.isdigit():
                    continue

                pid = int(pid_dir)
                p_info = self._get_process_info(pid)
                if p_info is None:
                    continue

                if not include_system and self._is_system_process(p_info):
                    continue

                processes.append(p_info)
        except Exception as e:
            print(f"[ZBLZ] Error scanning /proc: {e}")

        processes.sort(key=lambda p: p.name.lower())
        self._cache = processes
        return processes.copy()

    def scan_user_processes(self) -> List[ProcessInfo]:
        """
        Scan processes owned by the current user.

        Returns:
            Sorted list of user-space processes (non-system)
        """
        processes: List[ProcessInfo] = []

        try:
            for pid_dir in os.listdir('/proc'):
                if not pid_dir.isdigit():
                    continue

                pid = int(pid_dir)

                try:
                    if os.stat(f"/proc/{pid}").st_uid != self._current_uid:
                        continue
                except (FileNotFoundError, PermissionError, ProcessLookupError):
                    continue

                p_info = self._get_process_info(pid)
                if p_info is None:
                    continue

                if self._is_system_process(p_info):
                    continue

                processes.append(p_info)
        except Exception as e:
            print(f"[ZBLZ] Error scanning user processes: {e}")

        processes.sort(key=lambda p: p.name.lower())
        self._cache = processes
        return processes.copy()

    def scan_games_only(self) -> List[ProcessInfo]:
        """
        Scan only game-related processes (Wine/Proton/Steam heuristics).

        Returns:
            List of probable game processes
        """
        all_processes = self.scan_user_processes()

        game_processes = [
            p for p in all_processes
            if p.is_wine_process or p.is_proton_process or self._is_game_process(p)
        ]

        self._cache = game_processes
        return game_processes.copy()

    def find_by_name(self, name: str, partial: bool = True) -> List[ProcessInfo]:
        """Find processes by name from cache (or trigger a user scan)."""
        name_lower = name.lower()

        if not self._cache:
            self.scan_user_processes()

        if partial:
            return [p for p in self._cache if name_lower in p.name.lower()]

        return [p for p in self._cache if p.name.lower() == name_lower]

    def find_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Find a specific process by PID."""
        return self._get_process_info(pid)

    def _get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Read process information from /proc/<pid>."""
        proc_path = f"/proc/{pid}"

        try:
            with open(os.path.join(proc_path, "comm"), "r") as f:
                name = f.read().strip()

            with open(os.path.join(proc_path, "cmdline"), "r") as f:
                cmdline = f.read().replace("\x00", " ").strip()

            is_wine = self._is_wine_process(name, cmdline)
            is_proton = self._is_proton_process(name, cmdline)

            return ProcessInfo(
                pid=pid,
                name=name,
                cmdline=cmdline,
                is_wine_process=is_wine,
                is_proton_process=is_proton,
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            return None

    def _is_wine_process(self, name: str, cmdline: str) -> bool:
        """Check if process is Wine-related."""
        name_lower = name.lower()
        cmdline_lower = cmdline.lower()

        for indicator in self.WINE_INDICATORS:
            if indicator in name_lower or indicator in cmdline_lower:
                return True

        return name_lower.endswith(".exe")

    def _is_proton_process(self, name: str, cmdline: str) -> bool:
        """Check if process is Proton-related."""
        name_lower = name.lower()
        cmdline_lower = cmdline.lower()

        for indicator in self.PROTON_INDICATORS:
            if indicator in name_lower or indicator in cmdline_lower:
                return True

        return "compatdata" in cmdline_lower

    def _is_game_process(self, process: ProcessInfo) -> bool:
        """
        Check if process appears to be a game.

        Kept conservative to reduce false positives.
        """
        cmdline_lower = process.cmdline.lower()
        name_lower = process.name.lower()

        steam_indicators = ["steam_app", "steamapps/common", "compatdata"]
        for indicator in steam_indicators:
            if indicator in cmdline_lower:
                return True

        if name_lower.endswith(".exe"):
            return True

        cmd_parts = cmdline_lower.split()
        return bool(cmd_parts and cmd_parts[0].endswith(".exe"))

    def _is_system_process(self, process: ProcessInfo) -> bool:
        """Check if process is likely system/kernel level."""
        name_lower = process.name.lower()

        if name_lower in self.SYSTEM_PROCESSES:
            return True

        if name_lower.startswith(("kworker/", "irq/", "scsi_")):
            return True

        if not process.cmdline:
            return True

        return False

    def get_steam_games(self) -> List[ProcessInfo]:
        """Get list of running Steam game processes."""
        all_processes = self.scan_user_processes()

        return [
            p for p in all_processes
            if "steam_app" in p.cmdline.lower() or "steamapps/common" in p.cmdline.lower()
        ]

    def get_process_exe_path(self, pid: int) -> Optional[str]:
        """Get the executable path for a process."""
        try:
            return os.readlink(f"/proc/{pid}/exe")
        except (FileNotFoundError, PermissionError):
            return None

    def get_process_cwd(self, pid: int) -> Optional[str]:
        """Get the working directory for a process."""
        try:
            return os.readlink(f"/proc/{pid}/cwd")
        except (FileNotFoundError, PermissionError):
            return None
