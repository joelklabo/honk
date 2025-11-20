"""Process identification and naming utilities."""

import psutil
from typing import Optional, Dict, List, Tuple
from collections import defaultdict

from .pty_scanner import PTYProcess


def get_human_readable_name(pid: int, command: Optional[str]) -> str:
    """
    Extract a human-readable application name from process info.
    
    Attempts multiple strategies:
    1. For interpreters (node, python), extract the actual script/app name
    2. For Homebrew apps, use the package name
    3. Fallback to command name
    
    Args:
        pid: Process ID
        command: Command string from lsof
        
    Returns:
        Human-readable name (e.g., "node:copilot", "python:my-script", "bash")
    """
    if not command:
        return "unknown"
    
    try:
        proc = psutil.Process(pid)
        cmdline = proc.cmdline()
        
        # Strategy 1: For interpreters, extract actual application
        base_cmd = command.split('/')[-1].split()[0]
        
        # Node, Python, Ruby, etc - second arg is usually the real app
        interpreters = ['node', 'python', 'python3', 'ruby', 'perl']
        if base_cmd in interpreters and len(cmdline) >= 2:
            app_arg = cmdline[1]
            app_name = app_arg.split('/')[-1].split()[0]  # Remove path and args
            if app_name and app_name != base_cmd and not app_name.startswith('-'):
                return f"{base_cmd}:{app_name}"
        
        # Strategy 2: Check if Homebrew app
        exe = proc.exe()
        if 'homebrew' in exe.lower() or 'cellar' in exe.lower():
            parts = exe.split('/')
            if 'Cellar' in parts:
                idx = parts.index('Cellar')
                if idx + 1 < len(parts):
                    brew_name = parts[idx + 1]
                    # For node apps, still try to get the actual app
                    if brew_name in interpreters and len(cmdline) >= 2:
                        app_arg = cmdline[1]
                        app_name = app_arg.split('/')[-1].split()[0]
                        if app_name and not app_name.startswith('-'):
                            return f"{brew_name}:{app_name}"
                    return brew_name
        
        # Strategy 3: Fallback to basic command name
        return base_cmd
        
    except (psutil.NoSuchProcess, psutil.AccessDenied, IndexError):
        # Fallback if psutil fails
        return command.split('/')[-1].split()[0] if command else "unknown"


def get_application_pty_summary(processes: Dict[int, PTYProcess]) -> List[Dict]:
    """
    Aggregate PTY usage by application (not just by process).
    
    Groups processes by their human-readable application name
    and sums up total PTYs per application.
    
    Args:
        processes: Dict of PID -> PTYProcess
        
    Returns:
        List of dicts with application summaries, sorted by PTY count (highest first)
        Each dict contains:
            - application: Human-readable app name
            - total_ptys: Total PTYs across all processes for this app
            - process_count: Number of processes for this app
            - pids: List of PIDs belonging to this app
    """
    app_usage = defaultdict(lambda: {"total_ptys": 0, "pids": [], "process_count": 0})
    
    for pid, proc in processes.items():
        app_name = get_human_readable_name(pid, proc.command)
        app_usage[app_name]["total_ptys"] += proc.pty_count
        app_usage[app_name]["pids"].append(pid)
        app_usage[app_name]["process_count"] += 1
    
    # Convert to list and sort by total PTYs (descending)
    summary = [
        {
            "application": app_name,
            "total_ptys": stats["total_ptys"],
            "process_count": stats["process_count"],
            "pids": stats["pids"],
        }
        for app_name, stats in app_usage.items()
    ]
    
    summary.sort(key=lambda x: x["total_ptys"], reverse=True)
    return summary


def get_process_lineage(pid: int, max_depth: int = 10) -> List[Tuple[int, str]]:
    """
    Get the full process lineage (parent chain) for a process.
    
    Args:
        pid: Process ID to trace
        max_depth: Maximum depth to traverse (default 10)
        
    Returns:
        List of (pid, name) tuples from current process up to root
        Example: [(1234, "node:copilot"), (5678, "zsh"), (1, "launchd")]
    """
    lineage = []
    
    try:
        proc = psutil.Process(pid)
        
        # Add current process
        lineage.append((proc.pid, proc.name()))
        
        # Walk up the tree
        for ancestor in proc.parents():
            lineage.append((ancestor.pid, ancestor.name()))
            if len(lineage) >= max_depth:
                break
                
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    
    return lineage
