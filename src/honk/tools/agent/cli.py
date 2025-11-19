"""CLI commands for Honk Agent."""

import typer

from .validate import validate_app # Import the validate_app Typer instance
from .scaffold import scaffold_app # Import the scaffold_app Typer instance
from .template import template_app # Import the template_app Typer instance
from .list import list_app # Import the list_app Typer instance

agent_app = typer.Typer()

@agent_app.command("hello")
def hello():
    """A test command for the agent app."""
    typer.echo("Hello from agent app!")

agent_app.add_typer(validate_app, name="validate") # Add the validate_app to agent_app
agent_app.add_typer(scaffold_app, name="scaffold") # Add the scaffold_app to agent_app
agent_app.add_typer(template_app, name="template") # Add the template_app to agent_app
agent_app.add_typer(list_app, name="list") # Add the list_app to agent_app