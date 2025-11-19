"""Integration tests for honk agent list command."""
import pytest
from typer.testing import CliRunner
from pathlib import Path

from honk.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Set up test environment with mock directories."""
    import os
    
    # Mock Path.home()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    # Set up directories
    (tmp_path / ".github/agents").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".copilot/agents").mkdir(parents=True, exist_ok=True)
    
    # Change to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)


class TestAgentListIntegration:
    """Integration tests for honk agent list command."""

    def test_list_project_agents(self):
        """Should list agents in project directory."""
        # Arrange
        agent1 = """---
description: First test agent
---
# Agent 1
"""
        agent2 = """---
description: Second test agent
---
# Agent 2
"""
        Path(".github/agents/agent1.agent.md").write_text(agent1)
        Path(".github/agents/agent2.agent.md").write_text(agent2)
        
        # Act
        result = runner.invoke(app, ["agent", "list", "agents"])
        
        # Assert
        assert result.exit_code == 0
        assert "Project Agents" in result.stdout
        assert "agent1" in result.stdout
        assert "agent2" in result.stdout
        assert "First test agent" in result.stdout
        assert "Second test agent" in result.stdout
        assert "Total" in result.stdout and "2" in result.stdout

    def test_list_global_agents(self):
        """Should list agents in global directory with --location global."""
        # Arrange
        agent = """---
description: Global test agent
---
# Global Agent
"""
        global_dir = Path.home() / ".copilot/agents"
        (global_dir / "global-agent.agent.md").write_text(agent)
        
        # Act
        result = runner.invoke(
            app, 
            ["agent", "list", "agents", "--location", "global"]
        )
        
        # Assert
        assert result.exit_code == 0
        assert "Global Agents" in result.stdout
        assert "global-agent" in result.stdout
        assert "Global test agent" in result.stdout

    def test_list_all_agents(self):
        """Should list agents from both locations with --location all."""
        # Arrange
        project_agent = """---
description: Project agent
---
# Project
"""
        global_agent = """---
description: Global agent
---
# Global
"""
        Path(".github/agents/project.agent.md").write_text(project_agent)
        global_dir = Path.home() / ".copilot/agents"
        (global_dir / "global.agent.md").write_text(global_agent)
        
        # Act
        result = runner.invoke(
            app,
            ["agent", "list", "agents", "--location", "all"]
        )
        
        # Assert
        assert result.exit_code == 0
        assert "Project Agents" in result.stdout
        assert "Global Agents" in result.stdout
        assert "project" in result.stdout
        assert "global" in result.stdout
        assert "Total" in result.stdout and "2" in result.stdout

    def test_list_empty_directory(self):
        """Should handle empty directory gracefully."""
        # Act
        result = runner.invoke(app, ["agent", "list", "agents"])
        
        # Assert
        assert result.exit_code == 0
        assert "Project Agents" in result.stdout
        assert "No agents found" in result.stdout or "Total: 0 agent(s)" in result.stdout

    def test_list_truncates_long_descriptions(self):
        """Should truncate descriptions longer than 60 characters."""
        # Arrange
        agent = """---
description: This is a very long description that should be truncated because it exceeds the maximum length
---
# Long Desc Agent
"""
        Path(".github/agents/long.agent.md").write_text(agent)
        
        # Act
        result = runner.invoke(app, ["agent", "list", "agents"])
        
        # Assert
        assert result.exit_code == 0
        assert "..." in result.stdout  # Should show truncation
