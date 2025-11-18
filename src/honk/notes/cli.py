"""CLI commands for Honk Notes."""

import typer
from pathlib import Path
from typing import Optional
from .app import StreamingNotesApp
from .config import NotesConfig
from honk.ui import print_error, print_success, console

notes_app = typer.Typer()


@notes_app.command()
def edit(
    file: Optional[Path] = typer.Argument(
        None,
        help="File to edit (creates if doesn't exist)"
    ),
    idle_timeout: int = typer.Option(
        30,
        "--idle", "-i",
        help="Seconds of idle time before AI organization"
    ),
    no_auto_save: bool = typer.Option(
        False,
        "--no-auto-save",
        help="Disable auto-save"
    ),
    prompt: Optional[Path] = typer.Option(
        None,
        "--prompt", "-p",
        help="Custom AI prompt template file"
    ),
    # Agent-friendly flags
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Run in non-interactive mode (no TUI, for automation)"
    ),
    headless: bool = typer.Option(
        False,
        "--headless",
        help="Headless mode - no visual interface, API only"
    ),
    no_prompt: bool = typer.Option(
        False,
        "--no-prompt",
        help="Never prompt for input, fail fast on missing data"
    ),
    api_port: int = typer.Option(
        12345,
        "--api-port",
        help="IPC server port (for headless mode)"
    ),
):
    """
    Open AI-assisted notes editor.

    Examples:
        honk notes edit meeting.md
        honk notes edit --idle 60 notes.md
        honk notes edit --prompt custom.txt todo.md
        
    Agent-friendly examples:
        honk notes edit file.md --non-interactive
        honk notes edit --headless --api-port 12345
    """
    # Load custom prompt if specified
    prompt_template = None
    if prompt:
        if not prompt.exists():
            print_error(f"Prompt file not found: {prompt}")
            raise typer.Exit(1)
        prompt_template = prompt.read_text()

    # Create config
    config = NotesConfig(
        file_path=file,
        idle_timeout=idle_timeout,
        auto_save=not no_auto_save,
        prompt_template=prompt_template,
    )
    
    # Apply agent-friendly overrides
    config.non_interactive = non_interactive
    config.headless = headless
    config.no_prompt = no_prompt
    config.api_port = api_port
    
    # Handle non-interactive/headless modes
    if headless or non_interactive:
        from .headless import run_headless_mode
        return run_headless_mode(config)

    # Run app
    app = StreamingNotesApp(config)
    app.run()


@notes_app.command()
def organize(
    file: Path = typer.Argument(..., help="File to organize"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file (default: overwrite input)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print result without saving"
    ),
):
    """
    Organize notes file with AI (non-interactive).

    Examples:
        honk notes organize meeting.md
        honk notes organize notes.md -o organized.md
        honk notes organize --dry-run todo.md
    """
    import asyncio
    from .organizer import AIOrganizer

    if not file.exists():
        print_error(f"File not found: {file}")
        raise typer.Exit(1)

    content = file.read_text()
    organizer = AIOrganizer()

    # Run organization
    try:
        organized = asyncio.run(organizer.organize(content))

        if dry_run:
            console.print(organized)
        else:
            output_path = output or file
            output_path.write_text(organized)
            print_success(f"✓ Organized notes saved to {output_path}")

    except Exception as e:
        print_error(f"Organization failed: {e}")
        raise typer.Exit(1)


@notes_app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration"
    ),
):
    """
    Manage notes configuration.
    """
    config = NotesConfig.load()

    if show:
        console.print(config)
    else:
        typer.echo("Configuration management coming soon!")


@notes_app.command()
def agent_get(
    file: Path = typer.Argument(..., help="File to read"),
    what: str = typer.Option(
        "content",
        "--what",
        help="What to get: content, state, status"
    ),
):
    """
    Agent-friendly: Get information without opening editor.
    
    Examples:
        honk notes agent-get file.md --what content
        honk notes agent-get file.md --what state
    """
    import json
    import os
    
    if not file.exists():
        console.print(json.dumps({"error": "File not found"}))
        raise typer.Exit(1)
    
    if what == "content":
        console.print(file.read_text())
    
    elif what == "state":
        console.print(json.dumps({
            "exists": file.exists(),
            "size": file.stat().st_size,
            "modified": file.stat().st_mtime,
            "readable": os.access(file, os.R_OK),
            "writable": os.access(file, os.W_OK)
        }))
    
    elif what == "status":
        # TODO: Check if editor is running for this file
        console.print(json.dumps({"running": False}))
    
    else:
        console.print(json.dumps({"error": f"Unknown what: {what}"}))
        raise typer.Exit(1)


@notes_app.command()
def agent_set(
    file: Path = typer.Argument(..., help="File to write"),
    content: Optional[str] = typer.Option(
        None,
        "--content",
        help="New content"
    ),
    stdin: bool = typer.Option(
        False,
        "--stdin",
        help="Read from stdin"
    ),
):
    """
    Agent-friendly: Set content without opening editor.
    
    Examples:
        honk notes agent-set file.md --content "New content"
        echo "New content" | honk notes agent-set file.md --stdin
    """
    import json
    import sys
    
    if stdin:
        content = sys.stdin.read()
    
    if content is None:
        console.print(json.dumps({"error": "No content provided"}))
        raise typer.Exit(1)
    
    try:
        file.write_text(content)
        console.print(json.dumps({"success": True, "file": str(file)}))
    except Exception as e:
        console.print(json.dumps({"error": str(e)}))
        raise typer.Exit(1)


@notes_app.command()
def agent_organize(
    file: Path = typer.Argument(..., help="File to organize"),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Output file (default: overwrite input)"
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        help="Timeout in seconds"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview without writing"
    ),
):
    """
    Agent-friendly: Organize file without opening editor.
    
    Examples:
        honk notes agent-organize file.md
        honk notes agent-organize file.md --output organized.md
        honk notes agent-organize file.md --dry-run
    """
    import json
    import asyncio
    from .organizer import AIOrganizer
    
    if not file.exists():
        console.print(json.dumps({"error": "File not found"}))
        raise typer.Exit(1)
    
    try:
        content = file.read_text()
        organizer = AIOrganizer()
        
        organized = asyncio.run(organizer.organize(content))
        
        if dry_run:
            console.print(organized)
        else:
            output_file = output or file
            output_file.write_text(organized)
            console.print(json.dumps({
                "success": True,
                "file": str(output_file),
                "original_size": len(content),
                "organized_size": len(organized)
            }))
    
    except Exception as e:
        console.print(json.dumps({"error": str(e)}))
        raise typer.Exit(1)
