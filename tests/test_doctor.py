"""Tests for doctor pack engine."""

import json
from typer.testing import CliRunner

from honk.cli import app
from honk.internal.doctor import global_pack, get_pack, run_pack

runner = CliRunner()


def test_global_pack_runs():
    """Test that global pack runs successfully."""
    result = global_pack.run(plan=False)
    assert result.pack == "global"
    assert result.status in ["ok", "failed"]
    assert len(result.checks) > 0
    assert result.duration_ms > 0


def test_global_pack_checks():
    """Test that global pack includes expected checks."""
    result = global_pack.run()
    check_names = {check.name for check in result.checks}
    assert "os" in check_names
    assert "arch" in check_names
    assert "disk" in check_names
    assert "network" in check_names
    assert "tmp_dir" in check_names


def test_global_pack_plan_mode():
    """Test that plan mode works."""
    result = global_pack.run(plan=True)
    assert result.status in ["ok", "failed"]
    # Plan mode should still run checks, just not mutate


def test_pack_registry():
    """Test pack registration and retrieval."""
    pack = get_pack("global")
    assert pack is not None
    assert pack.name == "global"
    assert pack.requires == []


def test_run_pack():
    """Test running a pack through registry."""
    result = run_pack("global")
    assert result.pack == "global"
    assert result.duration_ms > 0


def test_doctor_command():
    """Test doctor command."""
    result = runner.invoke(app, ["doctor"])
    # Exit code may be 0 (all pass) or 10 (prereq failed)
    assert result.exit_code in [0, 10]
    assert "global" in result.stdout


def test_doctor_command_json():
    """Test doctor command with JSON output."""
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code in [0, 10]

    data = json.loads(result.stdout)
    assert "packs" in data
    assert len(data["packs"]) > 0
    assert data["packs"][0]["pack"] == "global"


def test_doctor_command_plan():
    """Test doctor command with plan flag."""
    result = runner.invoke(app, ["doctor", "--plan"])
    assert result.exit_code in [0, 10]
    assert "global" in result.stdout
