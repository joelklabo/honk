"""Main CLI application for honk."""
import sys
import json
import typer

from . import result

app = typer.Typer(add_completion=False)


@app.command()
def version():
    """Show version information."""
    print("honk version 0.1.0")
    print("result schema version: 1.0")


@app.command()
def info():
    """Show CLI information."""
    print("honk - Agent-first CLI for developer workflows")
    print("Python package: honk")


def main():
    """Entry point for the CLI."""
    try:
        app()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(result.EXIT_BUG)


if __name__ == "__main__":
    main()
