"""List command for honk agent."""
import typer
from pathlib import Path
from typing import Optional
import yaml

from honk.ui import console

list_app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=False
)


@list_app.callback()
def list_callback(ctx: typer.Context):
    """List available agents (defaults to 'agents' subcommand if none specified)."""
    if ctx.invoked_subcommand is None:
        # No subcommand specified, invoke agents command with default location
        ctx.invoke(list_agents, location="project")


@list_app.command("agents")
def list_agents(
    location: Optional[str] = typer.Option(
        "project",
        "--location", "-l",
        help="Location: 'project' (.github/agents), 'global' (~/.copilot/agents), or 'all'"
    )
):
    """
    List all available GitHub Copilot custom agents.
    
    Shows agent names and descriptions from project or global directories.
    Descriptions are extracted from agent YAML frontmatter.
    
    Locations:
      project - .github/agents/ (default, project-specific agents)
      global  - ~/.copilot/agents/ (user's personal agents)
      all     - Both project and global agents
    
    Examples:
      # List project agents
      honk agent list agents
      
      # List user's global agents
      honk agent list agents --location global
      
      # List all agents
      honk agent list agents -l all
    
    Output format:
      agent-name           - Description from YAML frontmatter
      
    Note: Long descriptions (>60 chars) are truncated with '...'
    """
    project_agents_dir = Path(".github/agents")
    global_agents_dir = Path.home() / ".copilot/agents"
    
    total_count = 0
    
    if location in ["project", "all"]:
        console.print("[bold]Project Agents[/bold] (.github/agents/):")
        if project_agents_dir.exists():
            agents = list(project_agents_dir.glob("*.agent.md"))
            if agents:
                for agent_file in sorted(agents):
                    name = agent_file.stem
                    description = _extract_description(agent_file)
                    console.print(f"  [info]{name:20}[/info] - {description}")
                    total_count += 1
            else:
                console.print("  [dim](No agents found)[/dim]")
        else:
            console.print("  [dim](Directory not found)[/dim]")
        console.print()
    
    if location in ["global", "all"]:
        console.print("[bold]Global Agents[/bold] (~/.copilot/agents/):")
        if global_agents_dir.exists():
            agents = list(global_agents_dir.glob("*.agent.md"))
            if agents:
                for agent_file in sorted(agents):
                    name = agent_file.stem
                    description = _extract_description(agent_file)
                    console.print(f"  [info]{name:20}[/info] - {description}")
                    total_count += 1
            else:
                console.print("  [dim](No agents found)[/dim]")
        else:
            console.print("  [dim](Directory not found)[/dim]")
        console.print()
    
    console.print(f"[bold]Total:[/bold] {total_count} agent(s)")


def _extract_description(agent_file: Path) -> str:
    """Extract description from agent YAML frontmatter."""
    try:
        content = agent_file.read_text()
        # Extract frontmatter
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            if frontmatter and "description" in frontmatter:
                desc = frontmatter["description"]
                # Truncate if too long
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                return desc
    except Exception:
        pass
    return "[dim](No description)[/dim]"
