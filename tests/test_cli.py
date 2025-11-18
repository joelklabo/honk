"""Tests for the CLI module."""

import json
from typer.testing import CliRunner

from honk.cli import app

runner = CliRunner()


def test_version_command():
    """Test version command outputs correctly."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "honk version 0.1.0" in result.stdout
    assert "result schema version: 1.0" in result.stdout


def test_version_command_json():
    """Test version command with --json flag."""
    result = runner.invoke(app, ["version", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["version"] == "1.0"
    assert data["status"] == "ok"
    assert "honk_version" in data["facts"]
    assert "schema_version" in data["facts"]


def test_info_command():
    """Test info command outputs correctly."""
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "honk" in result.stdout
    assert "Agent-first CLI" in result.stdout


def test_info_command_json():
    """Test info command with --json flag."""
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["version"] == "1.0"
    assert data["status"] == "ok"
    assert "name" in data["facts"]
    assert "package" in data["facts"]
