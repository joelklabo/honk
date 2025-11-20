"""Build ResultEnvelope from agent execution."""
from pathlib import Path
from typing import Optional
from honk.result import ResultEnvelope, Link
from honk.tools.agent.invoke_executor import ExecutionResult
import uuid
from datetime import datetime


def build_result_envelope(
    command: str,
    agent_name: str,
    prompt: str,
    context_files: Optional[list[Path]],
    execution_result: ExecutionResult,
) -> ResultEnvelope:
    """
    Build ResultEnvelope from agent execution result.
    
    Args:
        command: Full honk command executed
        agent_name: Name of agent invoked
        prompt: User prompt
        context_files: Context files provided
        execution_result: Result from AgentExecutor
    
    Returns:
        ResultEnvelope with structured output
    """
    # Determine status
    if execution_result.success:
        status = "ok"
        code = 0
    elif "authentication" in execution_result.error.lower():
        status = "needs_auth"
        code = 11
    elif "timeout" in execution_result.error.lower():
        status = "error"
        code = 30
    else:
        status = "error"
        code = 50
    
    # Build facts
    facts = {
        "agent_name": agent_name,
        "prompt": prompt,
        "output": execution_result.output,
    }
    
    if context_files:
        facts["context_files"] = [str(f) for f in context_files]  # type: ignore[assignment]
    
    if execution_result.error:
        facts["error"] = execution_result.error
    
    # Summary
    if status == "ok":
        summary = f"Agent '{agent_name}' executed successfully"
    elif status == "needs_auth":
        summary = f"Agent '{agent_name}' requires authentication"
    else:
        summary = f"Agent '{agent_name}' execution failed"
    
    # Links
    links = [
        Link(  # type: ignore[call-arg]
            title="Agent Documentation",
            href="https://docs.github.com/copilot/github-copilot-in-the-cli/using-github-copilot-in-the-cli#using-custom-agents",
        ),
    ]
    
    # Next steps
    next_commands = []
    if status == "needs_auth":
        next_commands.append("gh auth login")
    elif status == "ok" and "test" not in agent_name.lower():
        next_commands.append(f"honk agent invoke {agent_name} --context <more-files>")
    
    # Build envelope
    return ResultEnvelope(  # type: ignore[call-arg]
        version="1.0",
        command=command,  # type: ignore[arg-type]
        status=status,
        changed=False,  # Read-only operation
        code=code,  # type: ignore[arg-type]
        summary=summary,
        run_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat() + "Z",
        duration_ms=execution_result.duration_ms,
        facts=facts,
        links=links,
        next=next_commands,  # type: ignore[arg-type]
    )
