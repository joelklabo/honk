"""Tests for file locking."""

import os
import time
from pathlib import Path

import pytest

from honk.notes.file_lock import FileLockManager


def test_lock_manager_initialization():
    """Test lock manager can be initialized."""
    manager = FileLockManager()
    assert manager.acquired_locks == set()


def test_acquire_lock(tmp_path):
    """Test acquiring a lock."""
    manager = FileLockManager()
    test_file = tmp_path / "test.md"
    test_file.write_text("content")

    assert manager.acquire_lock(test_file)
    assert test_file in manager.acquired_locks

    # Lock file should exist
    lock_file = tmp_path / ".test.md.honk.lock"
    assert lock_file.exists()


def test_release_lock(tmp_path):
    """Test releasing a lock."""
    manager = FileLockManager()
    test_file = tmp_path / "test.md"
    test_file.write_text("content")

    manager.acquire_lock(test_file)
    manager.release_lock(test_file)

    assert test_file not in manager.acquired_locks

    # Lock file should be removed
    lock_file = tmp_path / ".test.md.honk.lock"
    assert not lock_file.exists()


def test_is_locked(tmp_path):
    """Test checking if file is locked."""
    manager1 = FileLockManager()
    manager2 = FileLockManager()
    test_file = tmp_path / "test.md"
    test_file.write_text("content")

    # Not locked initially
    assert not manager1.is_locked(test_file)

    # Acquire lock
    manager1.acquire_lock(test_file)

    # Own lock should not be considered "locked"
    assert not manager1.is_locked(test_file)

    # Another manager should see it as locked
    assert manager2.is_locked(test_file)


def test_stale_lock_detection(tmp_path):
    """Test detection of stale locks."""
    manager = FileLockManager()
    test_file = tmp_path / "test.md"
    test_file.write_text("content")

    # Create a lock with a non-existent PID
    lock_file = tmp_path / ".test.md.honk.lock"
    lock_file.write_text('{"pid": 999999, "hostname": "test", "timestamp": 0}')

    # Should detect as stale and allow acquisition
    assert manager.acquire_lock(test_file)
    assert test_file in manager.acquired_locks


def test_get_lock_info(tmp_path):
    """Test getting lock information."""
    manager = FileLockManager()
    test_file = tmp_path / "test.md"
    test_file.write_text("content")

    # No lock initially
    assert manager.get_lock_info(test_file) is None

    # Acquire lock
    manager.acquire_lock(test_file)

    # Get lock info
    info = manager.get_lock_info(test_file)
    assert info is not None
    assert info.pid == os.getpid()
    assert info.file_path == str(test_file.absolute())


def test_release_all(tmp_path):
    """Test releasing all locks."""
    manager = FileLockManager()
    file1 = tmp_path / "test1.md"
    file2 = tmp_path / "test2.md"
    file1.write_text("content1")
    file2.write_text("content2")

    manager.acquire_lock(file1)
    manager.acquire_lock(file2)

    assert len(manager.acquired_locks) == 2

    manager.release_all()

    assert len(manager.acquired_locks) == 0
    assert not (tmp_path / ".test1.md.honk.lock").exists()
    assert not (tmp_path / ".test2.md.honk.lock").exists()


def test_concurrent_lock_attempt(tmp_path):
    """Test that concurrent lock attempts fail."""
    manager1 = FileLockManager()
    manager2 = FileLockManager()
    test_file = tmp_path / "test.md"
    test_file.write_text("content")

    # First manager acquires lock
    assert manager1.acquire_lock(test_file)

    # Second manager cannot acquire
    assert not manager2.acquire_lock(test_file)
