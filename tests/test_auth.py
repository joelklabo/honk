"""Tests for auth subsystem."""
import pytest
from typer.testing import CliRunner

from honk.cli import app
from honk.auth import ensure_gh_auth, ensure_az_auth

runner = CliRunner()


def test_ensure_gh_auth():
    """Test GitHub auth check."""
    success, message = ensure_gh_auth()
    assert isinstance(success, bool)
    assert isinstance(message, str)
    assert len(message) > 0


def test_ensure_az_auth():
    """Test Azure DevOps auth check."""
    success, message = ensure_az_auth()
    assert isinstance(success, bool)
    assert isinstance(message, str)
    assert len(message) > 0


def test_auth_ensure_gh_command():
    """Test auth ensure-gh command."""
    result = runner.invoke(app, ["auth", "ensure-gh"])
    # Exit code should be 0 (ok) or 11 (needs_auth)
    assert result.exit_code in [0, 11]
    assert len(result.stdout) > 0


def test_auth_ensure_az_command():
    """Test auth ensure-az command."""
    result = runner.invoke(app, ["auth", "ensure-az"])
    # Exit code should be 0 (ok) or 11 (needs_auth)
    assert result.exit_code in [0, 11]
    assert len(result.stdout) > 0
