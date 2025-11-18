"""PTY scanner and process detection."""

import subprocess
import os
import signal
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PTYProcess:
    """Process holding PTY sessions."""
    pid: int
    command: str | None
    ptys: List[str]
    
    @property
    def pty_count(self) -> int:
        return len(self.ptys)


def run_lsof() -> str:
    """Execute lsof to enumerate PTYs."""
    try:
        return subprocess.check_output(
            ["lsof", "-FpcnT"],
            text=True,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return ""
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
                    ptys=[]
                )
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
    """Determine if process is a leak candidate."""
    if not proc.command:
        return False
    
    cmd = proc.command.lower()
    
    # Heuristic: copilot-like processes
    if "copilot" in cmd:
        return proc.pty_count > threshold
    if "node" in cmd and "copilot" in cmd:
        return proc.pty_count > threshold
    if "agent" in cmd and "copilot" in cmd:
        return proc.pty_count > threshold
    
    # Heavy users (fallback)
    return proc.pty_count > threshold * 2


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
