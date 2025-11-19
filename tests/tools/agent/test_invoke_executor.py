"""Unit tests for AgentExecutor."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess


def test_build_prompt_basic():
    """Test basic prompt building without context."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    executor = AgentExecutor("test-agent", {})
    prompt = executor._build_prompt("Generate user endpoints")
    
    assert prompt == "Generate user endpoints"


def test_build_prompt_with_single_context_file(tmp_path):
    """Test prompt building with one context file."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    # Create test context file
    context_file = tmp_path / "user.py"
    context_file.write_text("class User:\n    pass")
    
    executor = AgentExecutor("test-agent", {})
    prompt = executor._build_prompt(
        "Generate endpoints",
        context_files=[context_file]
    )
    
    assert "Generate endpoints" in prompt
    assert "Context:" in prompt
    assert f"File: {context_file}" in prompt
    assert "class User:" in prompt
    assert "```py" in prompt


def test_build_prompt_with_multiple_context_files(tmp_path):
    """Test prompt building with multiple context files."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    # Create test context files
    file1 = tmp_path / "user.py"
    file1.write_text("class User:\n    pass")
    
    file2 = tmp_path / "admin.py"
    file2.write_text("class Admin(User):\n    pass")
    
    executor = AgentExecutor("test-agent", {})
    prompt = executor._build_prompt(
        "Generate endpoints",
        context_files=[file1, file2]
    )
    
    assert "Generate endpoints" in prompt
    assert "Context:" in prompt
    assert f"File: {file1}" in prompt
    assert f"File: {file2}" in prompt
    assert "class User:" in prompt
    assert "class Admin(User):" in prompt


def test_build_prompt_preserves_file_extension_in_code_block(tmp_path):
    """Test that code blocks use correct syntax highlighting."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    # Test various file extensions
    py_file = tmp_path / "code.py"
    py_file.write_text("print('hello')")
    
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Title")
    
    json_file = tmp_path / "data.json"
    json_file.write_text('{"key": "value"}')
    
    executor = AgentExecutor("test-agent", {})
    
    # Python file
    prompt_py = executor._build_prompt("test", context_files=[py_file])
    assert "```py" in prompt_py
    
    # Markdown file
    prompt_md = executor._build_prompt("test", context_files=[md_file])
    assert "```md" in prompt_md
    
    # JSON file
    prompt_json = executor._build_prompt("test", context_files=[json_file])
    assert "```json" in prompt_json


def test_executor_initialization():
    """Test AgentExecutor initialization."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    agent_def = {
        "name": "test-agent",
        "description": "Test agent",
        "tools": ["read", "edit"]
    }
    
    executor = AgentExecutor(
        agent_name="test-agent",
        agent_definition=agent_def,
        timeout=300,
        log_file=None
    )
    
    assert executor.agent_name == "test-agent"
    assert executor.agent_definition == agent_def
    assert executor.timeout == 300
    assert executor.log_file is None


def test_executor_with_log_file(tmp_path):
    """Test AgentExecutor with log file."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    log_file = tmp_path / "test.log"
    
    executor = AgentExecutor(
        agent_name="test-agent",
        agent_definition={},
        log_file=log_file
    )
    
    assert executor.log_file == log_file


def test_log_writes_to_file(tmp_path):
    """Test that _log method writes to file."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    log_file = tmp_path / "test.log"
    
    executor = AgentExecutor(
        agent_name="test-agent",
        agent_definition={},
        log_file=log_file
    )
    
    executor._log("Test message")
    
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content
    # Should have timestamp
    assert "[" in content and "]" in content


def test_log_appends_to_existing_file(tmp_path):
    """Test that _log appends to existing file."""
    from honk.tools.agent.invoke_executor import AgentExecutor
    
    log_file = tmp_path / "test.log"
    log_file.write_text("Existing content\n")
    
    executor = AgentExecutor(
        agent_name="test-agent",
        agent_definition={},
        log_file=log_file
    )
    
    executor._log("New message")
    
    content = log_file.read_text()
    assert "Existing content" in content
    assert "New message" in content


def test_execution_result_dataclass():
    """Test ExecutionResult dataclass."""
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    result = ExecutionResult(
        success=True,
        output="Generated code",
        error="",
        duration_ms=1250,
        exit_code=0
    )
    
    assert result.success is True
    assert result.output == "Generated code"
    assert result.error == ""
    assert result.duration_ms == 1250
    assert result.exit_code == 0


def test_execution_result_with_error():
    """Test ExecutionResult with error."""
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    result = ExecutionResult(
        success=False,
        output="",
        error="Authentication required",
        duration_ms=500,
        exit_code=11
    )
    
    assert result.success is False
    assert result.output == ""
    assert result.error == "Authentication required"
    assert result.exit_code == 11
