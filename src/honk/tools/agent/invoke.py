"""Agent invocation command."""
import typer
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown

from honk.result import ResultEnvelope
from honk.tools.agent.invoke_executor import AgentExecutor
from honk.tools.agent.result_builder import build_result_envelope

console = Console()


def invoke_agent(
    agent_name: str = typer.Argument(..., help="Name of agent to invoke"),
    prompt: str = typer.Argument(..., help="Instruction for agent"),
    context: list[Path] = typer.Option(
        None, "--context", "-c",
        help="Context file(s) to include (can be used multiple times)"
    ),
    output_format: str = typer.Option(
        "text", "--output", "-o",
        help="Output format: json, text, markdown"
    ),
    timeout: int = typer.Option(
        300, "--timeout",
        help="Maximum execution time in seconds"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Show what would be executed without running"
    ),
    log_file: Path = typer.Option(
        None, "--log",
        help="Save execution log to file"
    ),
    json_output: bool = typer.Option(
        False, "--json",
        help="Output as JSON (alias for --output json)"
    ),
    no_color: bool = typer.Option(
        False, "--no-color",
        help="Disable colored output"
    ),
    plan: Path = typer.Option(
        None, "--plan",
        help="Custom plan file"
    ),
) -> None:
    """
    Invoke a GitHub Copilot agent programmatically.
    
    Examples:
        # Basic invocation
        honk agent invoke api-specialist "Generate user endpoints"
        
        # With context files
        honk agent invoke api-specialist "Generate endpoints" \\
            --context models/user.py \\
            --context tests/test_user.py
        
        # JSON output for CI/CD
        honk agent invoke test-generator "Generate tests" --json
        
        # Dry run to see what would execute
        honk agent invoke deployment-agent "Deploy to staging" --dry-run
    """
    # Resolve output format
    if json_output:
        output_format = "json"
    
    # Disable colors if requested
    if no_color:
        console._color_system = None
    
    # Validate agent exists
    agent_path = get_agent_path(agent_name)
    if not agent_path.exists():
        console.print(f"[red]Error:[/red] Agent '{agent_name}' not found")
        console.print(f"[dim]Hint:[/dim] Run 'honk agent list' to see available agents")
        raise typer.Exit(1)
    
    # Validate context files exist
    if context:
        for ctx_file in context:
            if not ctx_file.exists():
                console.print(f"[red]Error:[/red] Context file not found: {ctx_file}")
                raise typer.Exit(1)
    
    # Load agent definition
    agent_def = load_agent_definition(agent_path)
    
    # Dry run mode
    if dry_run:
        show_dry_run_info(agent_name, prompt, context, agent_def)
        return
    
    # Execute agent
    try:
        executor = AgentExecutor(
            agent_name=agent_name,
            agent_definition=agent_def,
            timeout=timeout,
            log_file=log_file,
        )
        
        result = executor.execute(prompt, context_files=context)
        
        # Build result envelope
        envelope = build_result_envelope(
            command=f"honk agent invoke {agent_name}",
            agent_name=agent_name,
            prompt=prompt,
            context_files=context,
            execution_result=result,
        )
        
        # Output in requested format
        if output_format == "json":
            print_json(envelope)
        elif output_format == "markdown":
            print_markdown_result(envelope)
        else:  # text
            print_text_result(envelope)
        
        # Exit with appropriate code
        raise typer.Exit(envelope.code)
        
    except TimeoutError:
        console.print("[red]Error:[/red] Agent execution timed out")
        raise typer.Exit(30)  # system error
    except Exception as e:
        console.print(f"[red]Error:[/red] Agent invocation failed: {e}")
        raise typer.Exit(50)  # bug


def get_agent_path(agent_name: str) -> Path:
    """Get path to agent definition file."""
    # Try local first: .github/agents/
    local_path = Path(".github/agents") / f"{agent_name}.agent.md"
    if local_path.exists():
        return local_path
    
    # Try global: ~/.copilot/agents/
    global_path = Path.home() / ".copilot/agents" / f"{agent_name}.agent.md"
    if global_path.exists():
        return global_path
    
    return local_path  # Return non-existent path for error handling


def load_agent_definition(agent_path: Path) -> dict:
    """Load and parse agent YAML frontmatter."""
    from honk.tools.agent.validate import YAMLFrontmatterValidator
    
    content = agent_path.read_text()
    validator = YAMLFrontmatterValidator()
    result = validator.validate(content)
    
    if not result.valid:
        console.print("[red]Error:[/red] Invalid agent definition:")
        for error in result.errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)
    
    return result.frontmatter


def show_dry_run_info(
    agent_name: str,
    prompt: str,
    context: list[Path],
    agent_def: dict,
) -> None:
    """Display what would be executed in dry-run mode."""
    console.print(Panel.fit(
        "[bold]Dry Run - No execution[/bold]",
        border_style="yellow"
    ))
    
    console.print("\n[bold]Agent:[/bold]", agent_name)
    console.print("[bold]Description:[/bold]", agent_def.get("description", "N/A"))
    console.print("[bold]Tools:[/bold]", ", ".join(agent_def.get("tools", [])))
    
    console.print("\n[bold]Prompt:[/bold]")
    console.print(f"  {prompt}")
    
    if context:
        console.print("\n[bold]Context Files:[/bold]")
        for ctx in context:
            console.print(f"  - {ctx}")
    
    console.print("\n[bold]Would execute:[/bold]")
    cmd = f"copilot @{agent_name} --input \"<prompt + context>\""
    syntax = Syntax(cmd, "bash", theme="monokai")
    console.print(syntax)


def print_json(envelope: ResultEnvelope) -> None:
    """Print result as JSON."""
    output = json.dumps(envelope.model_dump(), indent=2)
    print(output)


def print_text_result(envelope: ResultEnvelope) -> None:
    """Print result in human-readable text format."""
    # Status indicator
    status_color = {
        "ok": "green",
        "prereq_failed": "yellow",
        "needs_auth": "yellow",
        "error": "red",
    }.get(envelope.status, "white")
    
    console.print(f"\n[{status_color}]● {envelope.status.upper()}[/{status_color}]")
    console.print(f"[bold]{envelope.summary}[/bold]\n")
    
    # Facts section
    if envelope.facts:
        console.print("[bold]Results:[/bold]")
        table = Table(show_header=False, box=None)
        for key, value in envelope.facts.items():
            if key != "output":  # Handle output separately
                table.add_row(f"  {key}:", str(value))
        console.print(table)
    
    # Output section
    if "output" in envelope.facts and envelope.facts["output"]:
        console.print("\n[bold]Agent Output:[/bold]")
        console.print(Panel(envelope.facts["output"], border_style="blue"))
    
    # Links section
    if envelope.links:
        console.print("\n[bold]Learn More:[/bold]")
        for link in envelope.links:
            console.print(f"  • {link.title}: {link.href}")
    
    # Next steps
    if envelope.next:
        console.print("\n[bold]Next Steps:[/bold]")
        for cmd in envelope.next:
            console.print(f"  $ {cmd}")
    
    # Footer
    console.print(f"\n[dim]Completed in {envelope.duration_ms}ms[/dim]")


def print_markdown_result(envelope: ResultEnvelope) -> None:
    """Print result in markdown format."""
    md = f"""
# {envelope.summary}

**Status:** {envelope.status}  
**Duration:** {envelope.duration_ms}ms

## Results

"""
    
    if envelope.facts:
        for key, value in envelope.facts.items():
            md += f"- **{key}:** {value}\n"
    
    if envelope.links:
        md += "\n## Learn More\n\n"
        for link in envelope.links:
            md += f"- [{link.title}]({link.href})\n"
    
    if envelope.next:
        md += "\n## Next Steps\n\n"
        for cmd in envelope.next:
            md += f"```bash\n{cmd}\n```\n\n"
    
    console.print(Markdown(md))
