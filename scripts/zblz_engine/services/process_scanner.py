"""
ZBLZ Engine - Process Scanner
Scans running processes from /proc filesystem.
"""

import os
import re
from typing import List, Optional
from dataclasses import dataclass
from models.app_state import ProcessInfo


class ProcessScanner:
    """
    Scans running processes on Linux using /proc filesystem.
    Identifies Wine/Proton processes for game detection.
    """
    
    # Keywords to identify Wine/Proton processes
    WINE_INDICATORS = [
        "wine", "wine64", "wine-preloader", "wine64-preloader",
        "wineserver", "winedevice.exe", "services.exe"
    ]
    
    PROTON_INDICATORS = [
        "proton", "pressure-vessel", "steam-runtime"
    ]
    
    GAME_INDICATORS = [
        ".exe", "steam_app", "steamapps", "compatdata"
    ]
    
    # Processes to filter out (system processes)
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
    
    def scan_all(self, include_system: bool = False) -> List[ProcessInfo]:
        """
        Scan all running processes.
        
        Args:
            include_system: Include system processes (usually not needed)
        
        Returns:
            List of ProcessInfo objects
        """
        processes = []
        proc_dir = "/proc"
        
        try:
            for entry in os.listdir(proc_dir):
                if not entry.isdigit():
                    continue
                
                pid = int(entry)
                process_info = self._get_process_info(pid)
                
                if process_info is None:
                    continue
                
                # Filter system processes unless requested
                if not include_system and self._is_system_process(process_info):
                    continue
                
                processes.append(process_info)
        
        except PermissionError:
            pass
        except FileNotFoundError:
            pass
        
        # Sort by name, then by PID
        processes.sort(key=lambda p: (p.name.lower(), p.pid))
        
        self._cache = processes
        return processes
    
    def scan_games_only(self) -> List[ProcessInfo]:
        """
        Scan only for game-related processes (Wine/Proton/Steam).
        
        Returns:
            List of game processes
        """
        all_processes = self.scan_all(include_system=False)
        
        game_processes = [
            p for p in all_processes
            if p.is_wine_process or p.is_proton_process or self._is_game_process(p)
        ]
        
        return game_processes
    
    def find_by_name(self, name: str, partial: bool = True) -> List[ProcessInfo]:
        """
        Find processes by name.
        
        Args:
            name: Process name to search for
            partial: Allow partial matches
        
        Returns:
            Matching processes
        """
        name_lower = name.lower()
        
        if not self._cache:
            self.scan_all()
        
        if partial:
            return [p for p in self._cache if name_lower in p.name.lower()]
        else:
            return [p for p in self._cache if p.name.lower() == name_lower]
    
    def find_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Find a specific process by PID."""
        return self._get_process_info(pid)
    
    def _get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Read process information from /proc/{pid}."""
        proc_path = f"/proc/{pid}"
        
        try:
            # Read process name from comm
            comm_path = os.path.join(proc_path, "comm")
            with open(comm_path, "r") as f:
                name = f.read().strip()
            
            # Read command line
            cmdline_path = os.path.join(proc_path, "cmdline")
            with open(cmdline_path, "r") as f:
                cmdline = f.read().replace("\x00", " ").strip()
            
            # Check for Wine/Proton
            is_wine = self._is_wine_process(name, cmdline)
            is_proton = self._is_proton_process(name, cmdline)
            
            return ProcessInfo(
                pid=pid,
                name=name,
                cmdline=cmdline,
                is_wine_process=is_wine,
                is_proton_process=is_proton
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
        
        # Check for .exe in name (Wine processes)
        if name.endswith(".exe"):
            return True
        
        return False
    
    def _is_proton_process(self, name: str, cmdline: str) -> bool:
        """Check if process is Proton-related."""
        name_lower = name.lower()
        cmdline_lower = cmdline.lower()
        
        for indicator in self.PROTON_INDICATORS:
            if indicator in name_lower or indicator in cmdline_lower:
                return True
        
        # Check for Steam compatdata path
        if "compatdata" in cmdline_lower:
            return True
        
        return False
    
    def _is_game_process(self, process: ProcessInfo) -> bool:
        """Check if process appears to be a game."""
        cmdline_lower = process.cmdline.lower()
        
        for indicator in self.GAME_INDICATORS:
            if indicator in cmdline_lower:
                return True
        
        return False
    
    def _is_system_process(self, process: ProcessInfo) -> bool:
        """Check if process is a system process."""
        name_lower = process.name.lower()
        
        # Check exact name match
        if name_lower in self.SYSTEM_PROCESSES:
            return True
        
        # Check common patterns
        if name_lower.startswith(("kworker/", "irq/", "scsi_")):
            return True
        
        # Kernel threads have empty cmdline
        if not process.cmdline:
            return True
        
        return False
    
    def get_steam_games(self) -> List[ProcessInfo]:
        """
        Get list of running Steam games.
        
        Returns:
            List of Steam game processes
        """
        all_processes = self.scan_all()
        
        steam_games = []
        for p in all_processes:
            if "steam_app" in p.cmdline.lower() or \
               "steamapps/common" in p.cmdline.lower():
                steam_games.append(p)
        
        return steam_games
    
    def get_process_exe_path(self, pid: int) -> Optional[str]:
        """Get the executable path for a process."""
        try:
            exe_link = f"/proc/{pid}/exe"
            return os.readlink(exe_link)
        except (FileNotFoundError, PermissionError):
            return None
    
    def get_process_cwd(self, pid: int) -> Optional[str]:
        """Get the working directory for a process."""
        try:
            cwd_link = f"/proc/{pid}/cwd"
            return os.readlink(cwd_link)
        except (FileNotFoundError, PermissionError):
            return None
