"""Cross-platform file locking for Honk Notes."""

import json
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class FileLock:
    """Represents a file lock."""

    file_path: str
    lock_file: str
    pid: int
    hostname: str
    timestamp: float


class FileLockManager:
    """Manages file locks with stale lock detection."""

    def __init__(self):
        self.acquired_locks: set[Path] = set()

    def _get_lock_path(self, file_path: Path) -> Path:
        """Get lock file path for a given file.

        Args:
            file_path: Path to the file

        Returns:
            Path to the lock file
        """
        return file_path.parent / f".{file_path.name}.honk.lock"

    def _is_stale_lock(self, lock_file: Path) -> bool:
        """Check if a lock is stale (from dead process).

        Args:
            lock_file: Path to the lock file

        Returns:
            True if lock is stale and can be removed
        """
        try:
            data = json.loads(lock_file.read_text())
            pid = data.get("pid")

            if not pid:
                return True

            # Check if process exists
            if HAS_PSUTIL:
                return not psutil.pid_exists(pid)
            else:
                # Fallback: try to send signal 0 (doesn't actually send signal)
                try:
                    os.kill(pid, 0)
                    return False
                except OSError:
                    return True

        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            # Lock file is corrupt or missing, consider it stale
            return True

    def acquire_lock(self, file_path: Path) -> bool:
        """Acquire lock on a file.

        Args:
            file_path: Path to the file to lock

        Returns:
            True if lock acquired, False if already locked
        """
        lock_file = self._get_lock_path(file_path)

        # Check for existing lock
        if lock_file.exists():
            if self._is_stale_lock(lock_file):
                # Remove stale lock
                try:
                    lock_file.unlink()
                except OSError:
                    return False
            else:
                # Lock is active
                return False

        # Create lock with metadata
        lock_data = {
            "file": str(file_path.absolute()),
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "timestamp": time.time(),
        }

        try:
            lock_file.write_text(json.dumps(lock_data, indent=2))
            self.acquired_locks.add(file_path)
            return True
        except OSError:
            return False

    def release_lock(self, file_path: Path) -> None:
        """Release lock on a file.

        Args:
            file_path: Path to the file to unlock
        """
        lock_file = self._get_lock_path(file_path)

        try:
            if lock_file.exists():
                lock_file.unlink()
            self.acquired_locks.discard(file_path)
        except OSError:
            pass

    def is_locked(self, file_path: Path) -> bool:
        """Check if a file is locked by another process.

        Args:
            file_path: Path to check

        Returns:
            True if file is locked by another process
        """
        lock_file = self._get_lock_path(file_path)

        if not lock_file.exists():
            return False

        # Check if it's our own lock
        if file_path in self.acquired_locks:
            return False

        # Check if lock is stale
        if self._is_stale_lock(lock_file):
            return False

        return True

    def get_lock_info(self, file_path: Path) -> Optional[FileLock]:
        """Get information about a lock.

        Args:
            file_path: Path to the locked file

        Returns:
            FileLock object or None if not locked
        """
        lock_file = self._get_lock_path(file_path)

        if not lock_file.exists():
            return None

        try:
            data = json.loads(lock_file.read_text())
            return FileLock(
                file_path=data.get("file", str(file_path)),
                lock_file=str(lock_file),
                pid=data.get("pid", 0),
                hostname=data.get("hostname", "unknown"),
                timestamp=data.get("timestamp", 0),
            )
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def release_all(self) -> None:
        """Release all locks acquired by this manager."""
        for file_path in list(self.acquired_locks):
            self.release_lock(file_path)
