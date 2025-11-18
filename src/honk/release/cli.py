"""Release tool CLI commands."""

import typer
from rich.console import Console

app = typer.Typer(help="Release automation tools")
console = Console()


@app.command()
def status():
    """Show release status and current version."""
    console.print("[cyan]honk release status[/] - Coming soon!")
    console.print("This will show current version, pending commits, and release readiness.")


@app.command()
def preview():
    """Preview what a release would look like (dry run)."""
    console.print("[cyan]honk release preview[/] - Coming soon!")
    console.print("This will analyze commits and show recommended version bump + changelog.")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Release automation with AI assistance.
    
    Run interactive release workflow, or use specific commands for targeted actions.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand = run interactive release
        console.print("[yellow]Interactive release workflow - Coming soon![/]")
        console.print("\nThis will guide you through:")
        console.print("  1. Analyze commits")
        console.print("  2. Choose version bump (MAJOR/MINOR/PATCH)")
        console.print("  3. Generate changelog (with AI)")
        console.print("  4. Build and publish")
