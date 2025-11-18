"""Tests for --no-color flag and HONK_NO_COLOR environment variable."""

from typer.testing import CliRunner
from honk.cli import app

runner = CliRunner()


def test_no_color_flag_exists():
    """Test that --no-color flag is accepted."""
    result = runner.invoke(app, ["--no-color", "version"])
    assert result.exit_code == 0
    assert "honk version" in result.stdout


def test_no_color_env_var(monkeypatch):
    """Test that HONK_NO_COLOR environment variable is respected."""
    monkeypatch.setenv("HONK_NO_COLOR", "1")
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "honk version" in result.stdout


def test_no_color_flag_on_demo_command():
    """Test --no-color flag works on subcommands."""
    result = runner.invoke(app, ["--no-color", "demo", "hello"])
    assert result.exit_code == 0
    assert "Hello" in result.stdout


def test_no_color_flag_on_help():
    """Test --no-color flag works on help output."""
    result = runner.invoke(app, ["--no-color", "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_no_color_with_info_command():
    """Test --no-color flag with info command."""
    result = runner.invoke(app, ["--no-color", "info"])
    assert result.exit_code == 0
    assert "honk" in result.stdout
