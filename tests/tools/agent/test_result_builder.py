"""Unit tests for result envelope builder."""
import pytest
from pathlib import Path


def test_build_result_envelope_success():
    """Test building result envelope for successful execution."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    exec_result = ExecutionResult(
        success=True,
        output="Generated code successfully",
        error="",
        duration_ms=1250,
        exit_code=0
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke test-agent",
        agent_name="test-agent",
        prompt="Generate code",
        context_files=None,
        execution_result=exec_result
    )
    
    assert envelope.version == "1.0"
    assert envelope.command == "honk agent invoke test-agent"
    assert envelope.status == "ok"
    assert envelope.code == 0
    assert envelope.changed is False  # Read-only operation
    assert "test-agent" in envelope.summary
    assert "successfully" in envelope.summary.lower()
    assert envelope.duration_ms == 1250
    
    # Check facts
    assert envelope.facts["agent_name"] == "test-agent"
    assert envelope.facts["prompt"] == "Generate code"
    assert envelope.facts["output"] == "Generated code successfully"
    
    # Should have run_id and timestamp
    assert envelope.run_id is not None
    assert envelope.timestamp is not None


def test_build_result_envelope_with_context_files(tmp_path):
    """Test envelope includes context files in facts."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    context_file = tmp_path / "user.py"
    context_file.write_text("class User: pass")
    
    exec_result = ExecutionResult(
        success=True,
        output="Generated endpoints",
        error="",
        duration_ms=2000,
        exit_code=0
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke api-specialist",
        agent_name="api-specialist",
        prompt="Generate user endpoints",
        context_files=[context_file],
        execution_result=exec_result
    )
    
    assert "context_files" in envelope.facts
    assert str(context_file) in envelope.facts["context_files"]


def test_build_result_envelope_authentication_error():
    """Test envelope for authentication errors."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    exec_result = ExecutionResult(
        success=False,
        output="",
        error="Authentication required: Please run 'gh auth login'",
        duration_ms=500,
        exit_code=1
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke test-agent",
        agent_name="test-agent",
        prompt="Do something",
        context_files=None,
        execution_result=exec_result
    )
    
    assert envelope.status == "needs_auth"
    assert envelope.code == 11
    assert "authentication" in envelope.summary.lower()
    
    # Should have error in facts
    assert "error" in envelope.facts
    assert "Authentication required" in envelope.facts["error"]
    
    # Should suggest next step
    assert len(envelope.next) > 0
    assert any("gh auth login" in cmd for cmd in envelope.next)


def test_build_result_envelope_timeout_error():
    """Test envelope for timeout errors."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    exec_result = ExecutionResult(
        success=False,
        output="",
        error="Execution timeout after 300 seconds",
        duration_ms=300000,
        exit_code=1
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke slow-agent",
        agent_name="slow-agent",
        prompt="Do slow task",
        context_files=None,
        execution_result=exec_result
    )
    
    assert envelope.status == "error"
    assert envelope.code == 30  # Timeout code
    assert "error" in envelope.facts


def test_build_result_envelope_generic_error():
    """Test envelope for generic execution errors."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    exec_result = ExecutionResult(
        success=False,
        output="",
        error="Unknown error occurred",
        duration_ms=1000,
        exit_code=1
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke test-agent",
        agent_name="test-agent",
        prompt="Do something",
        context_files=None,
        execution_result=exec_result
    )
    
    assert envelope.status == "error"
    assert envelope.code == 50  # Generic error code
    assert "failed" in envelope.summary.lower()


def test_result_envelope_has_required_fields():
    """Test that all required fields are present."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    exec_result = ExecutionResult(
        success=True,
        output="Success",
        error="",
        duration_ms=1000,
        exit_code=0
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke test",
        agent_name="test",
        prompt="test",
        context_files=None,
        execution_result=exec_result
    )
    
    required_fields = [
        "version",
        "command",
        "status",
        "changed",
        "code",
        "summary",
        "run_id",
        "timestamp",
        "duration_ms"
    ]
    
    envelope_dict = envelope.model_dump()
    
    for field in required_fields:
        assert field in envelope_dict, f"Missing required field: {field}"
        assert envelope_dict[field] is not None, f"Field {field} is None"


def test_result_envelope_includes_documentation_links():
    """Test that envelope includes helpful documentation links."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    exec_result = ExecutionResult(
        success=True,
        output="Success",
        error="",
        duration_ms=1000,
        exit_code=0
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke test",
        agent_name="test",
        prompt="test",
        context_files=None,
        execution_result=exec_result
    )
    
    assert len(envelope.links) > 0
    assert any("docs.github.com" in link.href for link in envelope.links)


def test_result_envelope_timestamp_is_iso8601():
    """Test that timestamp is in ISO 8601 format."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    from datetime import datetime
    
    exec_result = ExecutionResult(
        success=True,
        output="Success",
        error="",
        duration_ms=1000,
        exit_code=0
    )
    
    envelope = build_result_envelope(
        command="honk agent invoke test",
        agent_name="test",
        prompt="test",
        context_files=None,
        execution_result=exec_result
    )
    
    # Should be able to parse timestamp
    timestamp = datetime.fromisoformat(envelope.timestamp.replace('Z', '+00:00'))
    assert timestamp is not None


def test_result_envelope_run_id_is_unique():
    """Test that each envelope gets a unique run_id."""
    from honk.tools.agent.result_builder import build_result_envelope
    from honk.tools.agent.invoke_executor import ExecutionResult
    
    exec_result = ExecutionResult(
        success=True,
        output="Success",
        error="",
        duration_ms=1000,
        exit_code=0
    )
    
    envelope1 = build_result_envelope(
        command="honk agent invoke test",
        agent_name="test",
        prompt="test",
        context_files=None,
        execution_result=exec_result
    )
    
    envelope2 = build_result_envelope(
        command="honk agent invoke test",
        agent_name="test",
        prompt="test",
        context_files=None,
        execution_result=exec_result
    )
    
    assert envelope1.run_id != envelope2.run_id
