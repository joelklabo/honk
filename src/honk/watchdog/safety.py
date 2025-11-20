"""Safety check utilities for PTY process management."""

import os
import psutil


def has_controlling_terminal(pid: int) -> bool:
    """
    Check if process has an active controlling terminal.
    
    This is the PRIMARY SAFETY CHECK. Processes with controlling terminals
    are active user sessions and should NEVER be killed.
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if process has a controlling terminal (DO NOT KILL)
        True if unable to check (fail-safe)
        False if no controlling terminal (potentially safe to kill)
    """
    try:
        proc = psutil.Process(pid)
        terminal = proc.terminal()
        return terminal is not None
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Fail-safe: if we can't check, assume it has terminal
        return True


def is_zombie(pid: int) -> bool:
    """
    Check if process is a zombie (defunct).
    
    Zombie processes are already dead and should be reaped.
    They can be safely killed to clean up the process table.
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if process is zombie (SHOULD be reaped)
        False otherwise
    """
    try:
        proc = psutil.Process(pid)
        return proc.status() == psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def is_orphan(pid: int) -> bool:
    """
    Check if process is orphaned (parent is launchd/init).
    
    Orphaned processes have had their parent die and been adopted by init.
    If they're holding PTYs, they're likely leaks.
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if parent is PID 1 (launchd on macOS)
        False otherwise
    """
    try:
        proc = psutil.Process(pid)
        return proc.ppid() == 1
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def is_in_own_tree(pid: int) -> bool:
    """
    Check if process is our own process or ancestor.
    
    CRITICAL SAFETY: Never kill our own process or any parent/grandparent,
    as that would kill ourselves.
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if pid is in our process tree (NEVER KILL)
        False otherwise
    """
    try:
        our_pid = os.getpid()
        
        # Check if it's our own process
        if pid == our_pid:
            return True
        
        # Check all ancestors
        our_proc = psutil.Process(our_pid)
        for ancestor in our_proc.parents():
            if ancestor.pid == pid:
                return True
                
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Fail-safe: if we can't check, assume it's in our tree
        return True


# List of critical system processes on macOS that should never be killed
CRITICAL_SYSTEM_PROCESSES = {
    'launchd',
    'kernel_task',
    'com.apple.xpc.launchd',
    'syslogd',
    'notifyd',
    'diskarbitrationd',
    'configd',
    'mDNSResponder',
    'SecurityServer',
    'WindowServer',
    'loginwindow',
    'systemstats',
    'UserEventAgent',
}


def is_system_critical(pid: int) -> bool:
    """
    Check if process is a critical system process.
    
    Critical processes include:
    - Low PIDs (< 100, typically system services)
    - Root-owned processes with critical names
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if process is system critical (NEVER KILL)
        False otherwise
    """
    # Very low PIDs are always system processes
    if pid < 100:
        return True
    
    try:
        proc = psutil.Process(pid)
        
        # Check if root-owned and in critical list
        if proc.username() == 'root':
            name = proc.name().lower()
            if name in CRITICAL_SYSTEM_PROCESSES:
                return True
                
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Fail-safe: if we can't check, assume it's critical
        return True
