"""Main CLI application for honk."""

import sys
import json
import os
import typer

from . import result
from . import registry
from .internal.doctor import register_pack, global_pack, run_all_packs
from .auth import ensure_gh_auth, ensure_az_auth
from .auth.cli import gh_app, az_app
from .watchdog.pty_cli import pty_app
from .system_cli import system_app
from .ui import console, print_success, print_error, print_info, print_dim

app = typer.Typer(add_completion=False)
auth_app = typer.Typer()
demo_app = typer.Typer()
watchdog_app = typer.Typer()

# Add auth sub-apps
auth_app.add_typer(gh_app, name="gh", help="GitHub authentication")
auth_app.add_typer(az_app, name="az", help="Azure DevOps authentication")

# Add watchdog sub-apps
watchdog_app.add_typer(pty_app, name="pty", help="PTY session monitoring")

app.add_typer(auth_app, name="auth")
app.add_typer(demo_app, name="demo")
app.add_typer(watchdog_app, name="watchdog", help="System health monitoring")
app.add_typer(system_app, name="system", help="System diagnostics suite")


# Register built-in doctor packs
register_pack(global_pack)


# Global callback to handle --no-color flag
@app.callback()
def main_callback(
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
        envvar="HONK_NO_COLOR",
    ),
):
    """Honk CLI - Agent-first developer workflows."""
    if no_color or os.getenv("NO_COLOR"):
        # Disable Rich colors globally
        from rich.console import Console
        Console._environ = {"TERM": "dumb"}
        os.environ["NO_COLOR"] = "1"


@app.command()
def version(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show version information."""
    if json_output:
        envelope = result.ResultEnvelope(
            command=["honk", "version"],
            status="ok",
            code="version.ok",
            summary="Version information",
            run_id="version",
            duration_ms=0,
            facts={
                "honk_version": "0.1.0",
                "schema_version": "1.0",
            },
        )
        print(envelope.model_dump_json(indent=2))
    else:
        print_info("honk version 0.1.0")
        print_dim("result schema version: 1.0")


@app.command()
def info(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show CLI information."""
    if json_output:
        envelope = result.ResultEnvelope(
            command=["honk", "info"],
            status="ok",
            code="info.ok",
            summary="CLI information",
            run_id="info",
            duration_ms=0,
            facts={
                "name": "honk",
                "description": "Agent-first CLI for developer workflows",
                "package": "honk",
            },
        )
        print(envelope.model_dump_json(indent=2))
    else:
        print_info("honk - Agent-first CLI for developer workflows")
        print_dim("Python package: honk")


@app.command()
def introspect(
    json_output: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
):
    """Emit command catalog with metadata for all commands."""
    schema = registry.get_introspection_schema()
    if json_output:
        print(schema.model_dump_json(indent=2))
    else:
        print_info(f"Commands: {len(schema.commands)}")
        for cmd in schema.commands:
            console.print(f"  [key]{'/'.join(cmd.full_path)}:[/key] [dim]{cmd.description}[/dim]")


@app.command("help-json")
def help_json(
    command: str = typer.Argument(help="Command to get help for (e.g., 'version' or 'introspect')"),
):
    """Get machine-readable help for a specific command."""
    from . import help as help_module

    command_path = ["honk", command]
    help_schema = help_module.get_command_help_from_registry(command_path)

    if help_schema:
        print(help_module.emit_help_json(help_schema))
    else:
        print(f"Error: Command '{command}' not found", file=sys.stderr)
        sys.exit(result.EXIT_BUG)


@app.command()
def doctor(
    plan: bool = typer.Option(False, "--plan", help="Run in plan mode (no mutations)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Run doctor packs to check prerequisites."""
    import uuid
    try:
        pack_results = run_all_packs(plan=plan)
        
        # Determine overall status
        has_failure = any(pr.status == "failed" for pr in pack_results)
        overall_status = "prereq_failed" if has_failure else "ok"
        exit_code = result.EXIT_PREREQ_FAILED if has_failure else result.EXIT_OK

        if json_output:
            # Convert doctor PackResults to result envelope PackResults
            envelope_pack_results = [
                result.PackResult(
                    pack=pr.pack,
                    status=pr.status,
                    duration_ms=pr.duration_ms
                )
                for pr in pack_results
            ]
            
            envelope = result.ResultEnvelope(
                command=["honk", "doctor"],
                status=overall_status,
                code=f"doctor.{overall_status}",
                summary=f"Ran {len(pack_results)} doctor pack(s)",
                run_id=str(uuid.uuid4()),
                duration_ms=sum(pr.duration_ms for pr in pack_results),
                facts={
                    "total_packs": len(pack_results),
                    "passed_packs": sum(1 for pr in pack_results if pr.status == "ok"),
                    "failed_packs": sum(1 for pr in pack_results if pr.status == "failed"),
                },
                pack_results=envelope_pack_results,
            )
            print(envelope.model_dump_json(indent=2))
        else:
            for pr in pack_results:
                if pr.status == "ok":
                    print_success(f"{pr.pack}: {pr.summary} ({pr.duration_ms}ms)")
                else:
                    print_error(f"{pr.pack}: {pr.summary} ({pr.duration_ms}ms)")
                for check in pr.checks:
                    if check.passed:
                        console.print(f"  ✓ {check.name}: {check.message}")
                    else:
                        console.print(f"  ✗ {check.name}: {check.message}")
                    if check.remedy:
                        print_dim(f"    → {check.remedy}")

        sys.exit(exit_code)

    except Exception as e:
        print(f"Error running doctor packs: {e}", file=sys.stderr)
        sys.exit(result.EXIT_BUG)


@auth_app.command("ensure-gh")
def auth_ensure_gh():
    """Ensure GitHub authentication is configured."""
    success, message = ensure_gh_auth()
    print(message)
    sys.exit(result.EXIT_OK if success else result.EXIT_NEEDS_AUTH)


@auth_app.command("ensure-az")
def auth_ensure_az():
    """Ensure Azure DevOps authentication is configured."""
    success, message = ensure_az_auth()
    print(message)
    sys.exit(result.EXIT_OK if success else result.EXIT_NEEDS_AUTH)


@demo_app.command("hello")
def demo_hello(
    name: str = typer.Option("World", "--name", help="Name to greet"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    plan: bool = typer.Option(False, "--plan", help="Run in plan mode (dry-run)"),
):
    """Demo command demonstrating full CLI contract with prereqs, result envelope, and flags."""
    from .demo.hello import run_hello

    # Run prereq checks first
    try:
        pack_results = run_all_packs(plan=plan)
        if any(pr.status == "failed" for pr in pack_results):
            if json_output:
                error = {
                    "status": "prereq_failed",
                    "message": "Prerequisites not met",
                    "pack_results": [pr.model_dump() for pr in pack_results],
                }
                print(json.dumps(error, indent=2))
            else:
                print_error("Prerequisites failed - run 'honk doctor' to diagnose")
            sys.exit(result.EXIT_PREREQ_FAILED)
    except Exception as e:
        print(f"Error checking prerequisites: {e}", file=sys.stderr)
        sys.exit(result.EXIT_BUG)

    # Run the command
    result_envelope = run_hello(name=name, json_output=json_output, plan=plan)

    if json_output:
        print(result_envelope.model_dump_json(indent=2))
    else:
        console.print(f"[emphasis]{result_envelope.facts['greeting']}[/emphasis]")
        if plan:
            print_dim("(Plan mode - no changes made)")

    sys.exit(result.EXIT_OK)


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
                    description="Display honk and schema versions",
                )
            ],
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
                    command="honk info", description="Display CLI details"
                )
            ],
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
                    help="Output as JSON",
                )
            ],
            examples=[
                registry.CommandExample(
                    command="honk introspect --json",
                    description="Get full command catalog as JSON",
                )
            ],
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
                    help="Command to get help for",
                )
            ],
            examples=[
                registry.CommandExample(
                    command="honk help-json version",
                    description="Get JSON help schema for version command",
                ),
                registry.CommandExample(
                    command="honk help-json introspect",
                    description="Get JSON help schema for introspect command",
                ),
            ],
        )
    )
    registry.register_command(
        registry.CommandMetadata(
            area="core",
            tool="doctor",
            action="run",
            full_path=["honk", "doctor"],
            description="Run doctor packs to check prerequisites",
            options=[
                registry.CommandOption(
                    names=["--plan"],
                    type_hint="bool",
                    default=False,
                    help="Run in plan mode (no mutations)",
                ),
                registry.CommandOption(
                    names=["--json"],
                    type_hint="bool",
                    default=False,
                    help="Output as JSON",
                ),
            ],
            prereqs=["global"],
            examples=[
                registry.CommandExample(
                    command="honk doctor", description="Run all doctor pack checks"
                ),
                registry.CommandExample(
                    command="honk doctor --plan",
                    description="Preview checks without making changes",
                ),
                registry.CommandExample(
                    command="honk doctor --json",
                    description="Get check results as JSON",
                ),
            ],
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
