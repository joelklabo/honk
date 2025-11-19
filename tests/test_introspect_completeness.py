"""Tests for introspect command completeness.

Tests that introspect returns ALL commands, including those in sub-apps.
"""

import json
import subprocess


def test_introspect_includes_all_top_level_commands():
    """Introspect must include all top-level commands."""
    result = subprocess.run(
        ["honk", "introspect", "--json"],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    data = json.loads(result.stdout)
    commands = data["commands"]
    
    # Get all unique top-level commands (second element in full_path)
    top_level = set()
    for cmd in commands:
        if len(cmd["full_path"]) >= 2:
            top_level.add(cmd["full_path"][1])
    
    # Must include all main commands we know exist
    expected_commands = {
        "version",
        "info", 
        "introspect",
        "help-json",
        "doctor",
        "demo",
        "watchdog",  # Currently missing!
        "system",    # Currently missing!
        "auth",      # Currently missing!
        "notes",     # Currently missing!
        "agent",     # Currently missing!
        "release",   # Currently missing!
    }
    
    missing = expected_commands - top_level
    assert not missing, f"Missing top-level commands: {missing}"


def test_introspect_includes_watchdog_pty_commands():
    """Introspect must include watchdog pty subcommands."""
    result = subprocess.run(
        ["honk", "introspect", "--json"],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    data = json.loads(result.stdout)
    
    # Find watchdog pty commands
    pty_commands = [
        cmd for cmd in data["commands"]
        if len(cmd["full_path"]) >= 4
        and cmd["full_path"][1] == "watchdog"
        and cmd["full_path"][2] == "pty"
    ]
    
    # Must include at least these pty commands
    pty_command_names = {cmd["full_path"][3] for cmd in pty_commands}
    expected_pty_commands = {"show", "clean", "watch", "daemon", "observer", "history"}
    
    missing = expected_pty_commands - pty_command_names
    assert not missing, f"Missing watchdog pty commands: {missing}"


def test_introspect_command_count():
    """Introspect should return 40+ commands (not just 6)."""
    result = subprocess.run(
        ["honk", "introspect", "--json"],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    data = json.loads(result.stdout)
    command_count = len(data["commands"])
    
    # Should have many more than the 6 currently returned
    assert command_count >= 40, f"Expected 40+ commands, got {command_count}"


def test_introspect_human_output():
    """Introspect without --json should show all commands."""
    result = subprocess.run(
        ["honk", "introspect"],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    output = result.stdout
    
    # Should mention watchdog commands
    assert "watchdog" in output.lower()
    assert "system" in output.lower()
