"""Tests for help-json functionality."""

import json
from typer.testing import CliRunner

from honk.cli import app

runner = CliRunner()


def test_help_json_version_command():
    """Test help-json for version command."""
    result = runner.invoke(app, ["help-json", "version"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert data["version"] == "1.0"
    assert data["command"] == ["honk", "version"]
    assert "Show version information" in data["description"]
    assert isinstance(data["examples"], list)


def test_help_json_introspect_command():
    """Test help-json for introspect command."""
    result = runner.invoke(app, ["help-json", "introspect"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert data["command"] == ["honk", "introspect"]
    assert len(data["options"]) > 0
    assert data["options"][0]["names"] == ["--json", "--no-json"]


def test_help_json_includes_examples():
    """Test that help-json output includes examples."""
    result = runner.invoke(app, ["help-json", "version"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert len(data["examples"]) > 0
    assert "command" in data["examples"][0]
    assert "description" in data["examples"][0]


def test_help_json_nonexistent_command():
    """Test help-json with non-existent command."""
    result = runner.invoke(app, ["help-json", "nonexistent"])
    assert result.exit_code != 0
