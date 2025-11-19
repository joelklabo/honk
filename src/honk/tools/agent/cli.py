"""CLI commands for Honk Agent."""

import typer

agent_app = typer.Typer()

@agent_app.command("hello")
def hello():
    """A test command for the agent app."""
    typer.echo("Hello from agent app!")
