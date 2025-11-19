"""PTY monitoring daemon - background service."""

import os
import sys
import json
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, asdict

from .pty_scanner import scan_ptys, kill_processes, get_heavy_users, get_suspected_leaks


@dataclass
class DaemonConfig:
    """Daemon configuration."""
    scan_interval: int = 30  # seconds
    auto_kill_threshold: int = 0  # 0 = disabled
    cache_file: Path = Path("tmp/pty-cache.json")
    pid_file: Path = Path("tmp/pty-daemon.pid")
    log_file: Path = Path("tmp/pty-daemon.log")


class PTYDaemon:
    """PTY monitoring daemon."""
    
    def __init__(self, config: DaemonConfig):
        self.config = config
        self.running = False
        self.scan_count = 0
        
    def is_running(self) -> tuple[bool, Optional[int]]:
        """Check if daemon is already running.
        
        Returns:
            (is_running, pid) tuple
        """
        if not self.config.pid_file.exists():
            return False, None
            
        try:
            pid = int(self.config.pid_file.read_text().strip())
            # Check if process exists
            os.kill(pid, 0)
            return True, pid
        except (ValueError, OSError, ProcessLookupError):
            # PID file exists but process is dead
            self.config.pid_file.unlink(missing_ok=True)
            return False, None
    
    def start(self) -> dict:
        """Start daemon as background process.
        
        Returns:
            Result dict with pid and status
        """
        is_running, pid = self.is_running()
        if is_running:
            return {
                "success": False,
                "error": f"Daemon already running (PID {pid})",
                "pid": pid
            }
        
        # Ensure directories exist
        self.config.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.config.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.config.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Fork daemon process
        try:
            # Use subprocess to create truly detached process
            process = subprocess.Popen(
                [sys.executable, "-m", "honk.watchdog.pty_daemon", 
                 "--scan-interval", str(self.config.scan_interval),
                 "--auto-kill-threshold", str(self.config.auto_kill_threshold),
                 "--cache-file", str(self.config.cache_file),
                 "--pid-file", str(self.config.pid_file),
                 "--log-file", str(self.config.log_file)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            
            # Give it a moment to start
            time.sleep(0.5)
            
            # Check if it actually started
            if process.poll() is not None:
                return {
                    "success": False,
                    "error": "Daemon failed to start",
                    "pid": None
                }
            
            return {
                "success": True,
                "pid": process.pid,
                "scan_interval": self.config.scan_interval,
                "auto_kill_threshold": self.config.auto_kill_threshold,
                "cache_file": str(self.config.cache_file),
                "log_file": str(self.config.log_file)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start daemon: {e}",
                "pid": None
            }
    
    def stop(self) -> dict:
        """Stop running daemon gracefully.
        
        Returns:
            Result dict with success status
        """
        is_running, pid = self.is_running()
        if not is_running:
            return {
                "success": False,
                "error": "Daemon not running"
            }
        
        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            
            # Wait up to 5 seconds for process to exit
            for _ in range(50):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except OSError:
                    # Process is dead
                    break
            else:
                # Still alive after 5s, force kill
                os.kill(pid, signal.SIGKILL)
            
            # Clean up PID file
            self.config.pid_file.unlink(missing_ok=True)
            
            return {
                "success": True,
                "pid": pid
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop daemon: {e}",
                "pid": pid
            }
    
    def status(self) -> dict:
        """Get daemon status.
        
        Returns:
            Status dict with running state and cache info
        """
        is_running, pid = self.is_running()
        
        result = {
            "running": is_running,
            "pid": pid
        }
        
        if is_running:
            # Check cache freshness
            if self.config.cache_file.exists():
                cache_mtime = self.config.cache_file.stat().st_mtime
                cache_age = time.time() - cache_mtime
                result["cache_age_seconds"] = int(cache_age)
                result["cache_stale"] = cache_age > (self.config.scan_interval * 2)
                
                try:
                    cache_data = json.loads(self.config.cache_file.read_text())
                    result["last_scan"] = cache_data.get("timestamp")
                    result["scan_count"] = cache_data.get("scan_number")
                except Exception:
                    result["cache_error"] = True
        
        return result
    
    def run_loop(self):
        """Main daemon loop (runs in background process)."""
        self.running = True
        
        # Write PID file
        self.config.pid_file.write_text(str(os.getpid()))
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)
        
        self._log("Daemon started")
        self._log(f"Scan interval: {self.config.scan_interval}s")
        self._log(f"Auto-kill threshold: {self.config.auto_kill_threshold}")
        
        try:
            while self.running:
                self._scan_and_cache()
                time.sleep(self.config.scan_interval)
        finally:
            self._cleanup()
    
    def _scan_and_cache(self):
        """Scan PTYs and write to cache."""
        try:
            self.scan_count += 1
            self._log(f"Scan #{self.scan_count} starting...")
            
            # Scan PTYs
            processes = scan_ptys()
            total_ptys = sum(p.pty_count for p in processes.values())
            heavy_users = get_heavy_users(processes, threshold=4)
            suspected_leaks = get_suspected_leaks(processes, threshold=4)
            
            # Auto-kill if threshold exceeded
            killed = []
            if self.config.auto_kill_threshold > 0:
                for proc in suspected_leaks:
                    if proc.pty_count >= self.config.auto_kill_threshold:
                        self._log(f"Auto-killing PID {proc.pid} ({proc.command}): {proc.pty_count} PTYs")
                        results = kill_processes([proc.pid])
                        if results.get(proc.pid):
                            killed.append(proc.pid)
            
            # Build cache data
            cache_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "scan_number": self.scan_count,
                "total_ptys": total_ptys,
                "process_count": len(processes),
                "processes": [
                    {
                        "pid": p.pid,
                        "command": p.command,
                        "pty_count": p.pty_count,
                        "ptys": p.ptys[:10]  # Limit to first 10
                    }
                    for p in processes.values()
                ],
                "heavy_users": [
                    {"pid": p.pid, "command": p.command, "pty_count": p.pty_count}
                    for p in heavy_users
                ],
                "suspected_leaks": [
                    {"pid": p.pid, "command": p.command, "pty_count": p.pty_count}
                    for p in suspected_leaks
                ],
                "auto_killed": killed
            }
            
            # Write atomically (write to temp, then rename)
            temp_file = self.config.cache_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(cache_data, indent=2))
            temp_file.rename(self.config.cache_file)
            
            self._log(f"Scan #{self.scan_count} complete: {total_ptys} PTYs, {len(processes)} processes")
            if killed:
                self._log(f"Auto-killed: {killed}")
                
        except Exception as e:
            self._log(f"Error during scan: {e}")
    
    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        self._log("Received shutdown signal")
        self.running = False
    
    def _cleanup(self):
        """Clean up on exit."""
        self._log("Daemon stopping...")
        self.config.pid_file.unlink(missing_ok=True)
        self._log("Daemon stopped")
    
    def _log(self, message: str):
        """Write to log file."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_line = f"[{timestamp}] {message}\n"
        
        with open(self.config.log_file, "a") as f:
            f.write(log_line)


def main():
    """CLI entry point for daemon background process."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-interval", type=int, default=30)
    parser.add_argument("--auto-kill-threshold", type=int, default=0)
    parser.add_argument("--cache-file", type=Path, default=Path("tmp/pty-cache.json"))
    parser.add_argument("--pid-file", type=Path, default=Path("tmp/pty-daemon.pid"))
    parser.add_argument("--log-file", type=Path, default=Path("tmp/pty-daemon.log"))
    
    args = parser.parse_args()
    
    config = DaemonConfig(
        scan_interval=args.scan_interval,
        auto_kill_threshold=args.auto_kill_threshold,
        cache_file=args.cache_file,
        pid_file=args.pid_file,
        log_file=args.log_file
    )
    
    daemon = PTYDaemon(config)
    daemon.run_loop()


if __name__ == "__main__":
    main()
