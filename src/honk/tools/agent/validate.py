import typer
from pathlib import Path
from typing import Optional

from honk.ui import print_success, print_error, print_info, console
from honk.internal.validation.yaml_validator import YAMLFrontmatterValidator

validate_app = typer.Typer()

@validate_app.command("agent")
def validate_agent(
    name: Optional[str] = typer.Argument(
        None,
        help="Agent name to validate (e.g., 'researcher')"
    ),
    all_agents: bool = typer.Option(
        False,
        "--all", "-a",
        help="Validate all agents in .github/agents/"
    ),
    strict: bool = typer.Option(
        False,
        "--strict", "-s",
        help="Strict mode: additional style and best practice checks (coming soon)"
    ),
):
    """
    Validate agent YAML frontmatter against GitHub Copilot schema.
    
    Checks that agent files have valid YAML frontmatter with required fields,
    proper tool specifications, and conform to GitHub's agent format.
    
    Validates:
      ✓ YAML syntax is correct
      ✓ Required 'description' field present (10-200 chars)
      ✓ Optional fields follow schema (name, tools, target, metadata)
      ✓ Tools are valid (read, edit, search, shell, web_search, or *)
      ✓ No extra unknown fields
    
    Examples:
      # Validate single agent
      honk agent validate agent researcher
      
      # Validate all agents
      honk agent validate agent --all
      
      # Strict mode (future: style checks)
      honk agent validate agent researcher --strict
    
    Exit codes:
      0 - All agents valid
      1 - One or more agents invalid
    
    Common errors:
      - Missing 'description' field (required)
      - Description too short (<10 chars) or too long (>200 chars)
      - Invalid tool name (must be read/edit/search/shell/web_search/*)
      - Malformed YAML syntax
      - Invalid name pattern (must be lowercase, numbers, hyphens only)
    """
    # Placeholder for agent file discovery logic
    # For now, assume agent files are in .github/agents/
    agent_dir = Path(".github/agents")
    if not agent_dir.exists():
        print_error(f"Agent directory not found: {agent_dir}")
        raise typer.Exit(1)

    validator = YAMLFrontmatterValidator(schema_path=Path("schemas/agent.v1.json"))
    
    agents_to_validate: List[Path] = []
    if all_agents:
        agents_to_validate = list(agent_dir.glob("*.agent.md"))
    elif name:
        agent_file = agent_dir / f"{name}.agent.md"
        if not agent_file.exists():
            print_error(f"Agent file not found: {agent_file}")
            raise typer.Exit(1)
        agents_to_validate.append(agent_file)
    else:
        print_error("Please specify an agent name or use --all to validate all agents.")
        raise typer.Exit(1)

    overall_success = True
    for agent_file in agents_to_validate:
        console.print(f"Validating [info]{agent_file.name}[/info]...")
        result = validator.validate_file(agent_file)
        
        if result.valid:
            print_success(f"✓ Validated: {agent_file.name}")
            # TODO: Add strict mode checks here
        else:
            overall_success = False
            print_error(f"✗ Validation failed for: {agent_file.name}")
            for error in result.errors:
                console.print(f"  [error]Error:[/error] {error}")
        
        # Placeholder for warnings (strict mode)
        if strict:
            print_info("  (Strict mode checks not yet implemented)")

    if not overall_success:
        raise typer.Exit(1)
