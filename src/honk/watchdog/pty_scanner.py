"""PTY scanner and process detection."""

import subprocess
import os
import signal
from typing import Dict, List
from dataclasses import dataclass

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class PTYProcess:
    """Process holding PTY sessions."""
    pid: int
    command: str | None
    ptys: List[str]
    parent_pid: int | None = None
    
    @property
    def pty_count(self) -> int:
        return len(self.ptys)


def run_lsof() -> str:
    """Execute lsof to enumerate PTYs."""
    import glob
    
    try:
        # Find all /dev/ttys* devices (terminal PTYs on macOS/BSD)
        pty_devices = glob.glob("/dev/ttys*")
        if not pty_devices:
            # No PTY devices found
            return ""
        
        # Scan only PTY devices to avoid hanging on large systems
        # -F: parseable output
        # -p: PID
        # -c: command name  
        # -n: file name
        # -R: parent PID (NEW!)
        # Note: lsof returns exit code 1 when some files can't be accessed,
        # but still outputs what it can, so we use run() instead of check_output()
        result = subprocess.run(
            ["lsof", "-FpcnR"] + pty_devices,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return result.stdout
    except FileNotFoundError:
        raise RuntimeError("lsof not found - install it via Homebrew or system package manager")


def parse_lsof_output(output: str) -> Dict[int, PTYProcess]:
    """Parse lsof output into process → PTY mapping."""
    processes: Dict[int, PTYProcess] = {}
    current_pid: int | None = None
    
    for line in output.splitlines():
        if line.startswith("p"):  # PID
            current_pid = int(line[1:])
            if current_pid not in processes:
                processes[current_pid] = PTYProcess(
                    pid=current_pid,
                    command=None,
                    ptys=[],
                    parent_pid=None
                )
        elif line.startswith("R"):  # Parent PID
            if current_pid and current_pid in processes:
                processes[current_pid].parent_pid = int(line[1:])
        elif line.startswith("c"):  # Command
            if current_pid and current_pid in processes:
                processes[current_pid].command = line[1:]
        elif line.startswith("n/dev/ttys"):  # PTY path
            if current_pid and current_pid in processes:
                processes[current_pid].ptys.append(line[1:])
    
    return processes


def scan_ptys() -> Dict[int, PTYProcess]:
    """Scan system for PTY usage."""
    output = run_lsof()
    return parse_lsof_output(output)


def is_leak_candidate(proc: PTYProcess, threshold: int = 4) -> bool:
    """Determine if process is a leak candidate.
    
    SAFETY: Never kill processes that have an active controlling TTY.
    This prevents killing active Copilot CLI sessions.
    """
    if not proc.command:
        return False
    
    # SAFETY CHECK: If process has a controlling TTY, it's active - don't kill it
    # Active sessions will have stdin/stdout connected to a terminal
    if HAS_PSUTIL:
        try:
            p = psutil.Process(proc.pid)
            # Check if process has a controlling terminal
            if p.terminal():
                return False  # Active session - DO NOT KILL
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # If we can't check, fall through to other heuristics
    
    cmd = proc.command.lower()
    
    # Raise threshold significantly for copilot processes (they legitimately use many PTYs)
    if "copilot" in cmd:
        return proc.pty_count > threshold * 5  # 20+ PTYs for copilot (was 4)
    if "node" in cmd and "copilot" in cmd:
        return proc.pty_count > threshold * 5  # 20+ PTYs
    if "agent" in cmd and "copilot" in cmd:
        return proc.pty_count > threshold * 5  # 20+ PTYs
    
    # Heavy users (fallback) - more conservative
    return proc.pty_count > threshold * 3  # 12+ PTYs (was 8)


def kill_processes(pids: List[int]) -> Dict[int, bool]:
    """Kill processes and return success status."""
    results = {}
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            results[pid] = True
        except ProcessLookupError:
            results[pid] = False  # Already dead
        except PermissionError:
            results[pid] = False  # Can't kill
    return results


def get_heavy_users(processes: Dict[int, PTYProcess], threshold: int = 4) -> List[PTYProcess]:
    """Find processes using more than threshold PTYs."""
    return [p for p in processes.values() if p.pty_count > threshold]


def get_suspected_leaks(processes: Dict[int, PTYProcess], threshold: int = 4) -> List[PTYProcess]:
    """Find suspected leak candidates."""
    return [p for p in processes.values() if is_leak_candidate(p, threshold)]
