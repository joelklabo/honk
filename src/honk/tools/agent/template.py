import typer
from pathlib import Path

from honk.ui import print_success, print_error, console
from honk.internal.validation.yaml_validator import YAMLFrontmatterValidator

template_app = typer.Typer()

BUILTIN_TEMPLATES_DIR = Path("src/honk/tools/agent/templates")
CUSTOM_TEMPLATES_DIR = Path.home() / ".copilot/honk/agent-templates"

@template_app.command("list")
def list_templates():
    """
    List all available agent templates (built-in and custom).
    
    Shows templates you can use with 'honk agent scaffold create --template <name>'.
    
    Built-in templates:
      - default         - Basic agent template
      - research        - Research and analysis specialist
      - test-writer     - Testing and QA specialist
      - code-reviewer   - Code review specialist
      - documentation   - Documentation specialist
      - refactor        - Refactoring specialist
      - debug           - Debugging specialist
      - architect       - Architecture and design specialist
    
    Custom templates:
      Located in ~/.copilot/honk/agent-templates/
      Add your own with: honk agent template add
    
    Example:
      honk agent template list
    """
    console.print("[bold]Available Agent Templates:[/bold]")
    
    console.print("\n[bold]Built-in:[/bold]")
    builtin_templates = list(BUILTIN_TEMPLATES_DIR.glob("*.agent.md"))
    if builtin_templates:
        for template_path in builtin_templates:
            name = template_path.stem.replace(".agent", "")
            console.print(f"  [info]{name}[/info]")
    else:
        console.print("  (No built-in templates found)")

    console.print("\n[bold]Custom (~/.copilot/honk/agent-templates/):[/bold]")
    if CUSTOM_TEMPLATES_DIR.exists():
        custom_templates = list(CUSTOM_TEMPLATES_DIR.glob("*.agent.md"))
        if custom_templates:
            for template_path in custom_templates:
                name = template_path.stem.replace(".agent", "")
                console.print(f"  [info]{name}[/info]")
        else:
            console.print("  (No custom templates found)")
    else:
        console.print("  (Custom templates directory not found)")

@template_app.command("show")
def show_template(
    name: str = typer.Argument(..., help="Template name (e.g., 'research', 'test-writer')")
):
    """
    Display the full content of a specific agent template.
    
    Shows the template file including YAML frontmatter and markdown instructions.
    Useful for understanding template structure before using it.
    
    Template variables (replaced during creation):
      ${AGENT_NAME}   - Agent name from --name
      ${DESCRIPTION}  - Description from --description
      ${TOOLS}        - Tool list from --tools
      ${TARGET}       - Target environment (default: github-copilot)
    
    Examples:
      # Show research template
      honk agent template show research
      
      # Show default template
      honk agent template show default
    
    Searches in order:
      1. Built-in templates (src/honk/tools/agent/templates/)
      2. Custom templates (~/.copilot/honk/agent-templates/)
    """
    template_path = BUILTIN_TEMPLATES_DIR / f"{name}.agent.md"
    if not template_path.exists():
        template_path = CUSTOM_TEMPLATES_DIR / f"{name}.agent.md"
        if not template_path.exists():
            print_error(f"Template '{name}' not found in built-in or custom locations.")
            raise typer.Exit(1)
    
    console.print(template_path.read_text())

@template_app.command("add")
def add_template(
    name: str = typer.Argument(..., help="Name for your custom template (e.g., 'my-template')"),
    from_file: Path = typer.Option(
        ...,
        "--from", "-f",
        help="Path to existing agent file to use as template source"
    ),
):
    """
    Create a custom template from an existing agent file.
    
    Takes an existing agent .agent.md file and saves it as a reusable template
    in your custom templates directory (~/.copilot/honk/agent-templates/).
    
    The source file must:
      ✓ Be a valid agent file with YAML frontmatter
      ✓ Pass schema validation
      ✓ Have proper markdown structure
    
    After adding, use with:
      honk agent scaffold create --template <name>
    
    Examples:
      # Save your researcher agent as a template
      honk agent template add my-research --from .github/agents/researcher.agent.md
      
      # Create template from user agent
      honk agent template add personal --from ~/.copilot/agents/my-agent.agent.md
    
    Validation:
      Source file is validated before being saved as template.
      If validation fails, template is not created.
    """
    if not from_file.exists():
        print_error(f"Source file not found: {from_file}")
        raise typer.Exit(1)
    
    CUSTOM_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    new_template_path = CUSTOM_TEMPLATES_DIR / f"{name}.agent.md"

    if new_template_path.exists():
        print_error(f"Custom template '{name}' already exists.")
        raise typer.Exit(1)
    
    # Validate source file before adding as template
    validator = YAMLFrontmatterValidator(schema_path=Path("schemas/agent.v1.json"))
    validation_result = validator.validate_file(from_file)

    if not validation_result.valid:
        print_error(f"Source file '{from_file}' is not a valid agent file:")
        for error in validation_result.errors:
            console.print(f"  [error]Error:[/error] {error}")
        raise typer.Exit(1)

    new_template_path.write_text(from_file.read_text())
    print_success(f"✓ Added custom template '{name}' from '{from_file}' to '{new_template_path}'")
