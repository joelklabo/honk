"""Tests for bash completion system."""

import json
from typer.testing import CliRunner
from honk.cli import app

runner = CliRunner()


def test_completion_generate_command_exists():
    """Should have completion generate command."""
    result = runner.invoke(app, ["completion", "generate", "--help"])
    assert result.exit_code == 0
    assert "Generate shell completion script" in result.stdout


def test_completion_generate_bash():
    """Should generate valid bash completion script."""
    result = runner.invoke(app, ["completion", "generate", "bash"])
    assert result.exit_code == 0
    
    # Check for bash completion markers
    assert "_honk_completion()" in result.stdout
    assert "complete -F _honk_completion honk" in result.stdout
    assert "COMPREPLY" in result.stdout


def test_completion_uses_introspect():
    """Should use honk introspect for dynamic command discovery."""
    result = runner.invoke(app, ["completion", "generate", "bash"])
    assert result.exit_code == 0
    
    # Script should call honk introspect
    assert "honk introspect --json" in result.stdout


def test_completion_install_instructions():
    """Should provide install instructions with --help."""
    result = runner.invoke(app, ["completion", "install", "--help"])
    assert result.exit_code == 0
    assert "installing shell completion" in result.stdout


def test_completion_install_bash():
    """Should provide bash install instructions."""
    result = runner.invoke(app, ["completion", "install", "bash"])
    assert result.exit_code == 0
    
    # Should include installation instructions
    assert "bash" in result.stdout.lower()
    assert "~/.bashrc" in result.stdout or "source" in result.stdout


def test_generated_script_handles_subcommands():
    """Should complete subcommands dynamically."""
    result = runner.invoke(app, ["completion", "generate", "bash"])
    assert result.exit_code == 0
    
    # Should handle multi-level commands
    script = result.stdout
    # Check script structure supports nested commands
    assert "case" in script.lower() or "if" in script.lower()


def test_generated_script_handles_options():
    """Should complete options like --json, --help."""
    result = runner.invoke(app, ["completion", "generate", "bash"])
    assert result.exit_code == 0
    
    # Should complete common options
    script = result.stdout
    assert "--json" in script or "options" in script.lower()


def test_completion_generate_zsh():
    """Should generate valid zsh completion script."""
    result = runner.invoke(app, ["completion", "generate", "zsh"])
    assert result.exit_code == 0
    
    # Check for zsh completion markers
    assert "#compdef honk" in result.stdout
    assert "_honk()" in result.stdout
    assert "_describe" in result.stdout or "_arguments" in result.stdout


def test_zsh_completion_uses_introspect():
    """Should use honk introspect for dynamic command discovery in zsh."""
    result = runner.invoke(app, ["completion", "generate", "zsh"])
    assert result.exit_code == 0
    
    # Script should call honk introspect
    assert "honk introspect --json" in result.stdout


def test_zsh_completion_handles_subcommands():
    """Should complete subcommands dynamically in zsh."""
    result = runner.invoke(app, ["completion", "generate", "zsh"])
    assert result.exit_code == 0
    
    # Should have zsh completion structure
    script = result.stdout
    assert "local -a" in script or "_describe" in script


def test_completion_install_zsh():
    """Should provide zsh install instructions."""
    result = runner.invoke(app, ["completion", "install", "zsh"])
    assert result.exit_code == 0
    
    # Should include zsh-specific instructions
    assert "zsh" in result.stdout.lower()
    assert "~/.zshrc" in result.stdout or "fpath" in result.stdout
