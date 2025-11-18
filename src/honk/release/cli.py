"""Release tool CLI commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from honk.shared.git import GitOperations
from honk.release.analyzer import CommitAnalyzer, ReleaseType
from honk.release.versioning.bumper import VersionBumper

app = typer.Typer(help="Release automation tools")
console = Console()


@app.command()
def status():
    """Show release status and current version."""
    try:
        git = GitOperations()
        bumper = VersionBumper()
        analyzer = CommitAnalyzer()
        
        current_version = git.get_current_version() or "0.0.0"
        commits = git.get_commits_since_last_tag()
        analysis = analyzer.analyze(commits)
        
        # Create status table
        table = Table(title="Release Status")
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Current Version", current_version)
        table.add_row("Commits Since Last Tag", str(len(commits)))
        table.add_row("Breaking Changes", str(len(analysis.breaking_changes)))
        table.add_row("Features", str(len(analysis.features)))
        table.add_row("Fixes", str(len(analysis.fixes)))
        table.add_row("Recommended Release", analysis.recommended_type.value.upper())
        
        new_version_obj = bumper.get_current_version().bump(analysis.recommended_type)
        table.add_row("Next Version", str(new_version_obj))
        
        console.print(table)
        
        # Show reasoning
        console.print("\n[bold]Reasoning:[/]")
        for reason in analysis.reasons:
            console.print(f"  • {reason}")
            
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def preview():
    """Preview what a release would look like (dry run)."""
    try:
        git = GitOperations()
        bumper = VersionBumper()
        analyzer = CommitAnalyzer()
        
        console.print("[cyan]Analyzing commits...[/]")
        commits = git.get_commits_since_last_tag()
        analysis = analyzer.analyze(commits)
        
        old_version, new_version = bumper.bump_version(
            analysis.recommended_type,
            dry_run=True
        )
        
        console.print(Panel(
            f"[bold]Release Preview[/]\n\n"
            f"Current: {old_version}\n"
            f"New: [green]{new_version}[/] ({analysis.recommended_type.value.upper()})\n"
            f"Commits: {len(commits)}",
            title="Preview",
            border_style="green"
        ))
        
        console.print("\n[bold]Summary:[/]")
        console.print(analyzer.get_summary(analysis))
        
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def patch(
    plan: bool = typer.Option(False, "--plan", help="Dry run, don't make changes")
):
    """Create a PATCH release (bug fixes only)."""
    _execute_release(ReleaseType.PATCH, plan)


@app.command()
def minor(
    plan: bool = typer.Option(False, "--plan", help="Dry run, don't make changes")
):
    """Create a MINOR release (new features)."""
    _execute_release(ReleaseType.MINOR, plan)


@app.command()
def major(
    plan: bool = typer.Option(False, "--plan", help="Dry run, don't make changes")
):
    """Create a MAJOR release (breaking changes)."""
    _execute_release(ReleaseType.MAJOR, plan)


def _execute_release(release_type: ReleaseType, dry_run: bool = False):
    """Execute release workflow."""
    try:
        git = GitOperations()
        bumper = VersionBumper()
        
        # Pre-flight checks
        if not git.is_working_tree_clean():
            console.print("[red]Error: Working tree is not clean![/]")
            console.print("Commit or stash changes before releasing.")
            raise typer.Exit(1)
        
        # Bump version
        old_version, new_version = bumper.bump_version(release_type, dry_run=dry_run)
        
        mode = "[yellow]DRY RUN[/]" if dry_run else "[green]RELEASE[/]"
        console.print(f"\n{mode} {release_type.value.upper()}: {old_version} → {new_version}\n")
        
        if dry_run:
            console.print("[yellow]No changes made (--plan mode)[/]")
        else:
            # Commit version changes
            files = [str(f.relative_to(Path.cwd())) for f in bumper.get_version_files()]
            commit_msg = f"chore(release): bump version to {new_version}"
            git.commit_files(files, commit_msg)
            
            # Create tag
            git.create_tag(str(new_version), f"Release {new_version}")
            
            console.print(f"[green]✓[/] Version bumped to {new_version}")
            console.print(f"[green]✓[/] Tag v{new_version} created")
            console.print("\n[bold]Next steps:[/]")
            console.print("  • Push commits: git push")
            console.print(f"  • Push tag: git push origin v{new_version}")
            
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Release automation with AI assistance.
    
    Run interactive release workflow, or use specific commands for targeted actions.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand = show status
        status()
