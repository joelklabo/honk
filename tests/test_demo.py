"""Tests for demo commands."""

import json
from typer.testing import CliRunner

from honk.cli import app
from honk.demo.hello import run_hello

runner = CliRunner()


def test_run_hello_basic():
    """Test run_hello function."""
    result = run_hello(name="Test")
    assert result.status == "ok"
    assert result.code == "demo.hello.ok"
    assert "Test" in result.facts["greeting"]
    assert result.facts["name"] == "Test"


def test_run_hello_plan_mode():
    """Test run_hello in plan mode."""
    result = run_hello(name="Test", plan=True)
    assert result.changed is False
    assert "Would greet" in result.facts["greeting"]


def test_run_hello_includes_links():
    """Test that result includes links."""
    result = run_hello()
    assert len(result.links) > 0
    assert result.links[0].rel == "docs"


def test_run_hello_includes_next_steps():
    """Test that result includes next steps."""
    result = run_hello()
    assert len(result.next) > 0
    assert result.next[0].run[0] == "honk"


def test_demo_hello_command():
    """Test demo hello command."""
    result = runner.invoke(app, ["demo", "hello"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.stdout


def test_demo_hello_with_name():
    """Test demo hello with custom name."""
    result = runner.invoke(app, ["demo", "hello", "--name", "Agent"])
    assert result.exit_code == 0
    assert "Hello, Agent!" in result.stdout


def test_demo_hello_json_output():
    """Test demo hello with JSON output."""
    result = runner.invoke(app, ["demo", "hello", "--json"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert data["status"] == "ok"
    assert data["code"] == "demo.hello.ok"
    assert "greeting" in data["facts"]


def test_demo_hello_plan_mode():
    """Test demo hello in plan mode."""
    result = runner.invoke(app, ["demo", "hello", "--plan"])
    assert result.exit_code == 0
    assert "Would greet" in result.stdout
    assert "Plan mode" in result.stdout
