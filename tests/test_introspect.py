"""Tests for introspection functionality."""
import json
import pytest
from typer.testing import CliRunner

from honk.cli import app
from honk import registry

runner = CliRunner()


def test_introspect_json_output():
    """Test introspect command with JSON output."""
    result = runner.invoke(app, ["introspect", "--json"])
    assert result.exit_code == 0
    
    data = json.loads(result.stdout)
    assert data["version"] == "1.0"
    assert "commands" in data
    assert len(data["commands"]) >= 3  # version, info, introspect at minimum


def test_introspect_text_output():
    """Test introspect command with text output."""
    result = runner.invoke(app, ["introspect", "--no-json"])
    assert result.exit_code == 0
    assert "Commands:" in result.stdout
    assert "honk/version" in result.stdout
    assert "honk/introspect" in result.stdout


def test_introspection_schema_structure():
    """Test introspection schema has correct structure."""
    schema = registry.get_introspection_schema()
    assert schema.version == "1.0"
    assert len(schema.commands) > 0
    
    # Check first command has required fields
    cmd = schema.commands[0]
    assert hasattr(cmd, "area")
    assert hasattr(cmd, "tool")
    assert hasattr(cmd, "action")
    assert hasattr(cmd, "full_path")
    assert hasattr(cmd, "description")


def test_command_metadata_includes_examples():
    """Test that command metadata includes examples."""
    schema = registry.get_introspection_schema()
    version_cmd = next(c for c in schema.commands if "version" in c.full_path)
    assert len(version_cmd.examples) > 0
    assert version_cmd.examples[0].command
    assert version_cmd.examples[0].description
