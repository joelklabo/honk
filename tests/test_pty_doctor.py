"""Tests for PTY doctor pack."""

import pytest
from honk.internal.doctor import pty_pack, get_pack, run_pack


def test_pty_pack_registered():
    """Test that PTY pack is registered."""
    pack = get_pack("pty")
    assert pack is not None
    assert pack.name == "pty"


def test_pty_pack_runs():
    """Test that PTY pack runs successfully."""
    result = pty_pack.run(plan=False)
    assert result.pack == "pty"
    assert result.status in ["ok", "failed"]
    assert len(result.checks) > 0
    assert result.duration_ms > 0


def test_pty_pack_checks():
    """Test that PTY pack includes expected checks."""
    result = pty_pack.run()
    check_names = {check.name for check in result.checks}
    assert "pty_limit" in check_names
    assert "pty_usage" in check_names
    assert "pty_processes" in check_names
    assert "heavy_users" in check_names
    assert "leak_candidates" in check_names


def test_pty_pack_limit_check():
    """Test that PTY limit check returns a valid limit."""
    result = pty_pack.run()
    limit_check = next((c for c in result.checks if c.name == "pty_limit"), None)
    assert limit_check is not None
    assert limit_check.passed is True
    assert "PTY limit:" in limit_check.message


def test_pty_pack_usage_check():
    """Test that PTY usage check returns valid data."""
    result = pty_pack.run()
    usage_check = next((c for c in result.checks if c.name == "pty_usage"), None)
    assert usage_check is not None
    assert "PTY usage:" in usage_check.message
    # Check contains percentage
    assert "%" in usage_check.message


def test_pty_pack_plan_mode():
    """Test that PTY pack works in plan mode."""
    result = pty_pack.run(plan=True)
    assert result.status in ["ok", "failed"]
    # Plan mode should still run checks


def test_run_pty_pack_through_registry():
    """Test running PTY pack through registry."""
    result = run_pack("pty")
    assert result.pack == "pty"
    assert result.duration_ms > 0
