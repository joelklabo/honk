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
    
    # Get all unique top-level commands (second element in full_path after "honk")
    # For direct commands: ["honk", "version"] -> "version"
    # For sub-app groups: ["honk", "watchdog", ...] -> "watchdog"
    top_level = set()
    for cmd in commands:
        if len(cmd["full_path"]) >= 2:
            # Extract the command/group name right after "honk"
            top_level.add(cmd["full_path"][1])
    
    # Must include all main commands we know exist
    # These are ALL at index [1] of full_path after "honk"
    expected_commands = {
        "version",      # Direct command
        "info",         # Direct command
        "introspect",   # Direct command
        "help-json",    # Direct command (with hyphen)
        "doctor",       # Direct command
        "demo",         # Sub-app group
        "watchdog",     # Sub-app group
        "system",       # Sub-app group
        "auth",         # Sub-app group
        "notes",        # Sub-app group
        "agent",        # Sub-app group
        "release",      # Sub-app group (added by release module)
    }
    
    missing = expected_commands - top_level
    
    # Debug output if test fails
    if missing:
        print(f"\nFound top-level commands: {sorted(top_level)}")
        print(f"Expected: {sorted(expected_commands)}")
        print(f"Missing: {sorted(missing)}")
        print("\nSample command paths:")
        for cmd in commands[:5]:
            print(f"  {cmd['full_path']}")
    
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
