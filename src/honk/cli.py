"""Main CLI application for honk."""
import sys
import json
import typer

from . import result
from . import registry

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


@app.command()
def introspect(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Output as JSON")
):
    """Emit command catalog with metadata for all commands."""
    schema = registry.get_introspection_schema()
    if json_output:
        print(schema.model_dump_json(indent=2))
    else:
        print(f"Commands: {len(schema.commands)}")
        for cmd in schema.commands:
            print(f"  {'/'.join(cmd.full_path)}: {cmd.description}")


@app.command("help-json")
def help_json(command: str = typer.Argument(..., help="Command to get help for (e.g., 'version' or 'introspect')")):
    """Get machine-readable help for a specific command."""
    from . import help as help_module
    
    command_path = ["honk", command]
    help_schema = help_module.get_command_help_from_registry(command_path)
    
    if help_schema:
        print(help_module.emit_help_json(help_schema))
    else:
        print(f"Error: Command '{command}' not found", file=sys.stderr)
        sys.exit(result.EXIT_BUG)


# Register built-in commands for introspection
def _register_builtins():
    """Register built-in commands in the registry."""
    registry.register_command(
        registry.CommandMetadata(
            area="core",
            tool="info",
            action="show",
            full_path=["honk", "version"],
            description="Show version information",
            examples=[
                registry.CommandExample(
                    command="honk version",
                    description="Display honk and schema versions"
                )
            ]
        )
    )
    registry.register_command(
        registry.CommandMetadata(
            area="core",
            tool="info",
            action="show",
            full_path=["honk", "info"],
            description="Show CLI information",
            examples=[
                registry.CommandExample(
                    command="honk info",
                    description="Display CLI details"
                )
            ]
        )
    )
    registry.register_command(
        registry.CommandMetadata(
            area="core",
            tool="introspect",
            action="show",
            full_path=["honk", "introspect"],
            description="Emit command catalog with metadata",
            options=[
                registry.CommandOption(
                    names=["--json", "--no-json"],
                    type_hint="bool",
                    default=True,
                    help="Output as JSON"
                )
            ],
            examples=[
                registry.CommandExample(
                    command="honk introspect --json",
                    description="Get full command catalog as JSON"
                )
            ]
        )
    )
    registry.register_command(
        registry.CommandMetadata(
            area="core",
            tool="help",
            action="json",
            full_path=["honk", "help-json"],
            description="Get machine-readable help for a specific command",
            arguments=[
                registry.CommandArgument(
                    name="command",
                    type_hint="str",
                    required=True,
                    help="Command to get help for"
                )
            ],
            examples=[
                registry.CommandExample(
                    command="honk help-json version",
                    description="Get JSON help schema for version command"
                ),
                registry.CommandExample(
                    command="honk help-json introspect",
                    description="Get JSON help schema for introspect command"
                )
            ]
        )
    )


_register_builtins()


def main():
    """Entry point for the CLI."""
    try:
        app()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(result.EXIT_BUG)


if __name__ == "__main__":
    main()
