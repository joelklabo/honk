"""Integration tests for honk agent validate command."""
import pytest
from typer.testing import CliRunner
from pathlib import Path
import json

from honk.cli import app
from honk.tools.agent import validate

runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Set up a clean test environment with mocked paths."""
    import os
    
    # Mock Path.home() for user-specific files
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # Mock validate module paths
    monkeypatch.setattr(validate, "Path", lambda x: tmp_path / x if not Path(x).is_absolute() else Path(x))
    
    # Set up directories
    (tmp_path / ".github/agents").mkdir(parents=True, exist_ok=True)
    (tmp_path / "schemas").mkdir(exist_ok=True)
    
    # Create schema
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
            "description": {"type": "string", "minLength": 10, "maxLength": 200},
            "tools": {
                "oneOf": [
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "string", "enum": ["*"]}
                ]
            }
        },
        "required": ["description"]
    }
    (tmp_path / "schemas/agent.v1.json").write_text(json.dumps(schema_content))
    
    # Change to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)


class TestAgentValidateIntegration:
    """Integration tests for honk agent validate command."""

    def test_validate_single_valid_agent(self):
        """Should validate a single valid agent successfully."""
        # Arrange - Create valid agent
        agent_content = """---
name: test-agent
description: A valid test agent for validation
tools:
  - read
  - edit
---

# Test Agent
"""
        agent_file = Path(".github/agents/test-agent.agent.md")
        agent_file.write_text(agent_content)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "test-agent"]
        )
        
        # Assert
        assert result.exit_code == 0
        assert "✓ Validated" in result.stdout
        assert "test-agent.agent.md" in result.stdout

    def test_validate_single_invalid_agent_missing_description(self):
        """Should fail validation for agent missing required description."""
        # Arrange - Create invalid agent (missing description)
        agent_content = """---
name: invalid-agent
tools:
  - read
---

# Invalid Agent
"""
        agent_file = Path(".github/agents/invalid-agent.agent.md")
        agent_file.write_text(agent_content)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "invalid-agent"]
        )
        
        # Assert
        assert result.exit_code == 1
        assert "✗ Validation failed" in result.stdout
        assert "description" in result.stdout.lower()

    def test_validate_single_invalid_agent_invalid_yaml(self):
        """Should fail validation for agent with invalid YAML."""
        # Arrange - Create agent with invalid YAML
        agent_content = """---
name: bad-yaml
description: "This has invalid YAML
tools:
  - read
  - edit
---

# Bad YAML Agent
"""
        agent_file = Path(".github/agents/bad-yaml.agent.md")
        agent_file.write_text(agent_content)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "bad-yaml"]
        )
        
        # Assert
        assert result.exit_code == 1
        assert "✗ Validation failed" in result.stdout or "invalid" in result.stdout.lower()

    def test_validate_agent_not_found(self):
        """Should fail gracefully when agent file doesn't exist."""
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "nonexistent"]
        )
        
        # Assert
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_validate_all_agents(self):
        """Should validate all agents in directory."""
        # Arrange - Create multiple agents
        valid_agent = """---
name: valid-agent
description: A valid agent for testing
tools:
  - read
---

# Valid Agent
"""
        invalid_agent = """---
name: invalid-agent
tools:
  - read
---

# Invalid Agent (missing description)
"""
        Path(".github/agents/valid-agent.agent.md").write_text(valid_agent)
        Path(".github/agents/invalid-agent.agent.md").write_text(invalid_agent)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "--all"]
        )
        
        # Assert
        assert result.exit_code == 1  # Should fail because one is invalid
        assert "valid-agent.agent.md" in result.stdout
        assert "invalid-agent.agent.md" in result.stdout
        assert "✓ Validated" in result.stdout  # Valid one passes
        assert "✗ Validation failed" in result.stdout  # Invalid one fails

    def test_validate_strict_mode(self):
        """Should apply strict validation when --strict flag is used."""
        # Arrange
        agent_content = """---
name: test-agent
description: A test agent for strict validation
tools:
  - read
---

# Test Agent
"""
        Path(".github/agents/test-agent.agent.md").write_text(agent_content)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "test-agent", "--strict"]
        )
        
        # Assert
        assert result.exit_code == 0
        # Note: Strict mode checks not implemented yet, but command should work
        assert "test-agent" in result.stdout

    def test_validate_no_agent_name_no_flag(self):
        """Should fail when no agent name or --all flag provided."""
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent"]
        )
        
        # Assert
        assert result.exit_code == 1
        assert "specify an agent name" in result.stdout.lower() or "required" in result.stdout.lower()

    def test_validate_agent_directory_not_exists(self, tmp_path, monkeypatch):
        """Should fail gracefully when .github/agents directory doesn't exist."""
        # Arrange - Remove agent directory
        import shutil
        
        agent_dir = Path(".github/agents")
        if agent_dir.exists():
            shutil.rmtree(agent_dir)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "test"]
        )
        
        # Assert
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "directory" in result.stdout.lower()

    def test_validate_valid_agent_with_all_optional_fields(self):
        """Should validate agent with all optional fields populated."""
        # Arrange
        agent_content = """---
name: full-agent
description: A complete agent with all fields
target: github-copilot
tools:
  - read
  - edit
  - search
mcp-servers:
  custom:
    - tool1
    - tool2
metadata:
  owner: test-team
  version: "1.0.0"
  category: testing
  created: "2025-11-19"
---

# Full Agent
"""
        Path(".github/agents/full-agent.agent.md").write_text(agent_content)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "full-agent"]
        )
        
        # Assert
        assert result.exit_code == 0
        assert "✓ Validated" in result.stdout

    def test_validate_empty_agents_directory(self):
        """Should handle empty agents directory gracefully."""
        # Arrange - Ensure directory is empty
        agent_dir = Path(".github/agents")
        for f in agent_dir.glob("*.agent.md"):
            f.unlink()
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "validate", "agent", "--all"]
        )
        
        # Assert
        # Should succeed but not validate anything
        assert result.exit_code == 0 or "no agents" in result.stdout.lower()
