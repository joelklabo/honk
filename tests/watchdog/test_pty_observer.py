"""Tests for PTY observer TUI."""

import json
from pathlib import Path


def test_observer_cache_file_format(tmp_path):
    """Test expected cache file format."""
    cache_file = tmp_path / "cache.json"
    
    # Expected cache structure
    cache_data = {
        "timestamp": "2025-11-19T08:00:00Z",
        "scan_number": 42,
        "total_ptys": 100,
        "process_count": 10,
        "processes": [
            {"pid": 1234, "command": "node", "pty_count": 50}
        ],
        "heavy_users": [
            {"pid": 1234, "command": "node", "pty_count": 50}
        ],
        "suspected_leaks": [],
        "auto_killed": []
    }
    
    # Write and read back
    cache_file.write_text(json.dumps(cache_data, indent=2))
    loaded = json.loads(cache_file.read_text())
    
    # Verify structure
    assert "timestamp" in loaded
    assert "scan_number" in loaded
    assert "total_ptys" in loaded
    assert "processes" in loaded
    assert isinstance(loaded["processes"], list)


def test_observer_run_function_exists():
    """Test that run_observer function is importable."""
    from honk.watchdog.pty_observer import run_observer
    
    # Function should exist and be callable
    assert callable(run_observer)


def test_observer_command_available():
    """Test that observer command is registered."""
    from honk.watchdog.pty_cli import pty_app
    
    # Check that observer command exists
    commands = {cmd.name for cmd in pty_app.registered_commands}
    assert "observer" in commands
