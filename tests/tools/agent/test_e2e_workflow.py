"""End-to-end workflow tests for honk agent commands."""
import pytest
from typer.testing import CliRunner
from pathlib import Path
import json

from honk.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Set up clean test environment."""
    import os
    from honk.tools.agent import scaffold
    
    # Mock paths
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(scaffold, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(scaffold, "TEMPLATE_BASE_DIR", tmp_path / "src/honk/tools/agent/templates")
    monkeypatch.setattr(scaffold, "SCHEMA_AGENT_V1_PATH", tmp_path / "schemas/agent.v1.json")
    
    # Set up directories
    (tmp_path / ".github/agents").mkdir(parents=True, exist_ok=True)
    (tmp_path / "schemas").mkdir(exist_ok=True)
    (tmp_path / "src/honk/tools/agent/templates").mkdir(parents=True, exist_ok=True)
    
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
    
    # Create default template
    template_content = """---
name: ${AGENT_NAME}
description: ${DESCRIPTION}
tools:
  ${TOOLS}
---

# ${AGENT_NAME} Agent Instructions

You are ${AGENT_NAME}.
Your purpose: ${DESCRIPTION}
"""
    (tmp_path / "src/honk/tools/agent/templates/default.agent.md").write_text(template_content)
    
    # Change to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)


class TestEndToEndWorkflow:
    """Complete workflow tests for honk agent tool."""

    def test_complete_workflow_create_validate_list(self):
        """
        Complete workflow: Create agent → Validate it → List it.
        
        This tests the entire user journey:
        1. User creates new agent with scaffold
        2. User validates the agent
        3. User lists all agents to confirm it's there
        """
        # Step 1: Create agent
        create_result = runner.invoke(
            app,
            [
                "agent", "scaffold", "create",
                "--name", "workflow-test",
                "--description", "Testing complete workflow",
                "--tools", "read,edit"
            ]
        )
        
        assert create_result.exit_code == 0, f"Create failed: {create_result.stdout}"
        assert "✓ Created agent" in create_result.stdout
        
        # Step 2: Validate the created agent
        validate_result = runner.invoke(
            app,
            ["agent", "validate", "agent", "workflow-test"]
        )
        
        assert validate_result.exit_code == 0, f"Validate failed: {validate_result.stdout}"
        assert "✓ Validated" in validate_result.stdout
        
        # Step 3: List agents to confirm it's there
        list_result = runner.invoke(
            app,
            ["agent", "list", "agents"]
        )
        
        assert list_result.exit_code == 0, f"List failed: {list_result.stdout}"
        assert "workflow-test" in list_result.stdout
        assert "Testing complete workflow" in list_result.stdout

    def test_workflow_multiple_agents(self):
        """
        Test workflow with multiple agents.
        
        Create several agents, validate all, list all.
        """
        # Create multiple agents
        for i in range(3):
            result = runner.invoke(
                app,
                [
                    "agent", "scaffold", "create",
                    "--name", f"agent{i}",
                    "--description", f"Test agent number {i}",
                    "--tools", "read"
                ]
            )
            assert result.exit_code == 0
        
        # Validate all agents
        validate_result = runner.invoke(
            app,
            ["agent", "validate", "agent", "--all"]
        )
        
        assert validate_result.exit_code == 0
        assert "agent0" in validate_result.stdout
        assert "agent1" in validate_result.stdout
        assert "agent2" in validate_result.stdout
        
        # List all agents
        list_result = runner.invoke(
            app,
            ["agent", "list", "agents"]
        )
        
        assert list_result.exit_code == 0
        assert "Total" in list_result.stdout and "3" in list_result.stdout

    def test_workflow_error_handling(self):
        """
        Test workflow handles errors gracefully.
        
        Try to validate non-existent agent, create duplicate, etc.
        """
        # Try to validate non-existent agent
        validate_result = runner.invoke(
            app,
            ["agent", "validate", "agent", "does-not-exist"]
        )
        
        assert validate_result.exit_code == 1
        assert "not found" in validate_result.stdout.lower()
        
        # Create an agent
        create_result = runner.invoke(
            app,
            [
                "agent", "scaffold", "create",
                "--name", "test-agent",
                "--description", "Test agent for error handling",
                "--tools", "read"
            ]
        )
        
        assert create_result.exit_code == 0
        
        # Try to create duplicate
        duplicate_result = runner.invoke(
            app,
            [
                "agent", "scaffold", "create",
                "--name", "test-agent",
                "--description", "Duplicate agent",
                "--tools", "edit"
            ]
        )
        
        assert duplicate_result.exit_code == 1
        assert "already exists" in duplicate_result.stdout.lower()

    def test_workflow_template_integration(self):
        """
        Test workflow with template commands.
        
        List templates, use template to create agent.
        """
        # List templates
        template_list_result = runner.invoke(
            app,
            ["agent", "template", "list"]
        )
        
        assert template_list_result.exit_code == 0
        assert "default" in template_list_result.stdout
        
        # Create agent using default template
        create_result = runner.invoke(
            app,
            [
                "agent", "scaffold", "create",
                "--name", "template-test",
                "--description", "Created from template",
                "--tools", "search",
                "--template", "default"
            ]
        )
        
        assert create_result.exit_code == 0
        
        # Validate it worked
        validate_result = runner.invoke(
            app,
            ["agent", "validate", "agent", "template-test"]
        )
        
        assert validate_result.exit_code == 0
