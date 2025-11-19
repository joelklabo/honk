"""CLI commands for Honk Agent.

Manage GitHub Copilot CLI custom agents for your project.

Common workflows:
  1. Create new agent:    honk agent scaffold create --name researcher --description "..." --tools read,search
  2. Validate agents:     honk agent validate agent --all
  3. List agents:         honk agent list agents
  4. Manage templates:    honk agent template list

Learn more: https://docs.github.com/copilot/customizing-copilot/creating-custom-agents
"""

import typer

from .validate import validate_app
from .scaffold import scaffold_app
from .template import template_app
from .list import list_app

agent_app = typer.Typer(
    help="Manage GitHub Copilot CLI custom agents",
    no_args_is_help=True,
    rich_markup_mode="rich"
)

# Add sub-commands with helpful descriptions
agent_app.add_typer(
    scaffold_app,
    name="scaffold",
    help="Create new agents from templates"
)
agent_app.add_typer(
    validate_app,
    name="validate",
    help="Validate agent YAML frontmatter against schema"
)
agent_app.add_typer(
    list_app,
    name="list",
    help="List available agents in project or globally"
)
agent_app.add_typer(
    template_app,
    name="template",
    help="Manage agent templates (list, show, add)"
)