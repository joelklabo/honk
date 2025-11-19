import typer
from pathlib import Path
from typing import Optional, List
import os

from honk.ui import print_success, print_error, print_info, console
from honk.internal.templates.engine import TemplateEngine
from honk.internal.validation.yaml_validator import YAMLFrontmatterValidator

scaffold_app = typer.Typer()

# Calculate project root dynamically
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
TEMPLATE_BASE_DIR = PROJECT_ROOT / "src/honk/tools/agent/templates"
SCHEMA_AGENT_V1_PATH = PROJECT_ROOT / "schemas/agent.v1.json"

@scaffold_app.command("create")
def create_agent(
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Name for the new agent (e.g., 'researcher')."
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description", "-d",
        help="Brief description of what the agent does."
    ),
    tools: Optional[str] = typer.Option(
        None,
        "--tools", "-t",
        help="Comma-separated list of tools the agent can use (e.g., 'read,search'). Use '*' for all."
    ),
    location: str = typer.Option(
        "project",
        "--location", "-l",
        help="Where to create the agent: 'project' (.github/agents), 'user' (~/.copilot/agents)."
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template", "-T",
        help="Name of a built-in or custom template to use (e.g., 'research', 'test-writer')."
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive", "-i",
        help="Run in interactive mode to be prompted for details."
    ),
):
    """
    Generate a new custom agent from template or interactive prompts.
    """
    if not interactive and (not name or not description or not tools):
        print_error("In non-interactive mode, --name, --description, and --tools are required.")
        raise typer.Exit(1)

    # Determine agent file path
    agent_dir: Path
    if location == "project":
        agent_dir = PROJECT_ROOT / ".github/agents"
    elif location == "user":
        agent_dir = Path.home() / ".copilot/agents"
    else:
        print_error(f"Invalid location: {location}. Must be 'project' or 'user'.")
        raise typer.Exit(1)
    
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Handle interactive mode
    if interactive:
        if not name:
            name = typer.prompt("Enter agent name (kebab-case, e.g., 'my-agent')")
        if not description:
            description = typer.prompt("Enter agent description")
        if not tools:
            tools = typer.prompt("Enter comma-separated tools (e.g., 'read,search', or '*' for all)")
        if not template:
            template = typer.prompt("Enter template name (optional, e.g., 'research', 'test-writer')")

    if not name:
        print_error("Agent name is required.")
        raise typer.Exit(1)
    
    agent_file_name = f"{name}.agent.md"
    agent_file_path = agent_dir / agent_file_name

    if agent_file_path.exists():
        print_error(f"Agent file already exists: {agent_file_path}")
        raise typer.Exit(1)

    # Prepare context for template rendering
    tools_list = [t.strip() for t in tools.split(',')] if tools != "*" else ["*"]
    
    tools_yaml_formatted: str
    if tools_list == ["*"]:
        tools_yaml_formatted = "*"
    else:
        # Format as YAML list items with proper indentation
        # Template has "tools:\n  ${TOOLS}" so we need "- item\n  - item"
        tools_yaml_formatted = "- " + "\n  - ".join(tools_list)

    context = {
        "AGENT_NAME": name,
        "DESCRIPTION": description,
        "TOOLS": tools_yaml_formatted, # Pass formatted YAML string
        "TARGET": "github-copilot", # Default target
        "VERSION": "0.1.0", # Initial version
        "CAPABILITIES": "", # Placeholder, can be enhanced later
        "MEMORY_ENABLED": "false", # Default, research template overrides
        "MEMORY_LOCATION": "", # Default, research template overrides
    }

    # Move TemplateEngine instantiation inside the function
    template_engine = TemplateEngine(template_dir=TEMPLATE_BASE_DIR)
    
    template_to_use = f"{template}.agent.md" if template else "default.agent.md" # Assuming a default template
    if not template:
        # Create a very basic default template if none specified
        default_template_path = TEMPLATE_BASE_DIR / "default.agent.md"
        if not default_template_path.exists():
            default_template_path.write_text(f"""---
name: ${AGENT_NAME}
description: ${DESCRIPTION}
target: ${TARGET}
tools:
${TOOLS}
---

# ${AGENT_NAME} Agent Instructions

You are a custom agent named ${AGENT_NAME}.
Your purpose is: ${DESCRIPTION}
You have access to the following tools: ${TOOLS}
""")
            
    try:
        rendered_content = template_engine.render(template_to_use, context)
    except FileNotFoundError:
        print_error(f"Template '{template_to_use}' not found. Available templates are: {', '.join([p.stem.replace('.agent', '') for p in template_engine.template_dir.glob('*.agent.md')])}")
        raise typer.Exit(1)
    except KeyError as e:
        print_error(f"Missing context variable for template '{template_to_use}': {e}. Please provide all required options or use --interactive.")
        raise typer.Exit(1)

    # Validate rendered content before writing
    # Create a temporary file for validation
    temp_file = agent_dir / f".tmp_{agent_file_name}"
    temp_file.write_text(rendered_content)
    
    validator = YAMLFrontmatterValidator(schema_path=SCHEMA_AGENT_V1_PATH)
    validation_result = validator.validate_file(temp_file)
    temp_file.unlink() # Clean up temporary file

    if not validation_result.valid:
        print_error(f"Generated agent content is invalid:")
        for error in validation_result.errors:
            console.print(f"  [error]Error:[/error] {error}")
        raise typer.Exit(1)

    # Write the agent file
    agent_file_path.write_text(rendered_content)
    print_success(f"✓ Created agent: {agent_file_path}")
    print_success(f"✓ Validated YAML schema")

    # Add to git if in project location
    if location == "project":
        try:
            # This assumes git is initialized and .github/agents is tracked
            os.system(f"git add {agent_file_path}")
            print_success(f"✓ Added to git staging")
        except Exception as e:
            print_info(f"Could not add to git staging: {e}")

    print_info("\nNext steps:")
    print_info(f"  1. Review and customize: {agent_file_path}")
    print_info(f"  2. Test agent: honk agent test {name}")
    print_info(f"  3. Commit changes: git commit -m \"Add {name} agent\"")