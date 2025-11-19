"""Automatic command discovery from Typer apps.

This module walks Typer app structures to automatically discover all commands
without requiring manual registration.
"""

import typer
from typing import Any
from ..registry import CommandMetadata, CommandOption, CommandArgument, CommandExample


def discover_commands_from_app(
    app: typer.Typer,
    parent_path: list[str] | None = None,
    area: str = "core"
) -> list[CommandMetadata]:
    """Recursively discover all commands from a Typer app.
    
    Args:
        app: Typer application to inspect
        parent_path: Parent command path (e.g., ["honk", "watchdog"])
        area: Command area/category for organization
        
    Returns:
        List of CommandMetadata for all discovered commands
    """
    if parent_path is None:
        parent_path = []
    
    commands = []
    
    # Debug: Print what we're discovering (uncomment for debugging)
    import sys
    print(f"DEBUG: Discovering from {parent_path}, app has {len(app.registered_commands)} direct commands, {len(app.registered_groups)} sub-apps", file=sys.stderr)
    
    # Discover direct commands in this app
    for command_info in app.registered_commands:
        cmd_name = command_info.name or ""
        full_path = parent_path + [cmd_name]
        
        # Extract command metadata
        callback = command_info.callback
        description = (callback.__doc__ or "").strip().split("\n")[0] if callback else ""
        
        # Extract options and arguments from click context
        # Note: This is simplified - full implementation would inspect the click command
        options = _extract_options(command_info)
        arguments = _extract_arguments(command_info)
        
        metadata = CommandMetadata(
            area=area,
            tool=cmd_name,
            action="run",
            full_path=full_path,
            description=description,
            options=options,
            arguments=arguments,
            examples=_generate_basic_examples(full_path),
        )
        commands.append(metadata)
    
    # Recursively discover commands from sub-apps (Typer groups)
    for group_info in app.registered_groups:
        group_name = group_info.name or ""
        subapp = group_info.typer_instance
        
        # Recurse with extended path
        subcommands = discover_commands_from_app(
            subapp,
            parent_path=parent_path + [group_name],
            area=_determine_area(group_name)
        )
        commands.extend(subcommands)
    
    return commands


def _extract_options(command_info: Any) -> list[CommandOption]:
    """Extract command options from Typer command info.
    
    This inspects the click command to find all options/flags.
    """
    options = []
    
    try:
        # Access the click command from Typer
        if hasattr(command_info, 'click_command') and command_info.click_command:
            click_cmd = command_info.click_command
            for param in click_cmd.params:
                if isinstance(param, typer.click.Option):
                    option = CommandOption(
                        names=list(param.opts),
                        type_hint=str(param.type),
                        required=param.required,
                        default=param.default,
                        help=param.help or "",
                    )
                    options.append(option)
    except (AttributeError, Exception):
        # Fallback: return empty if we can't inspect
        pass
    
    return options


def _extract_arguments(command_info: Any) -> list[CommandArgument]:
    """Extract command arguments from Typer command info."""
    arguments = []
    
    try:
        if hasattr(command_info, 'click_command') and command_info.click_command:
            click_cmd = command_info.click_command
            for param in click_cmd.params:
                if isinstance(param, typer.click.Argument):
                    argument = CommandArgument(
                        name=param.name,
                        type_hint=str(param.type),
                        required=param.required,
                        default=param.default,
                        help=param.help or "",
                    )
                    arguments.append(argument)
    except (AttributeError, Exception):
        pass
    
    return arguments


def _generate_basic_examples(full_path: list[str]) -> list[CommandExample]:
    """Generate basic example for a command."""
    command_str = " ".join(full_path)
    return [
        CommandExample(
            command=command_str,
            description=f"Run {full_path[-1]} command"
        )
    ]


def _determine_area(group_name: str) -> str:
    """Determine command area from group name."""
    area_mapping = {
        "watchdog": "monitoring",
        "system": "diagnostics",
        "auth": "authentication",
        "agent": "ai",
        "notes": "ai",
        "release": "development",
        "demo": "demo",
    }
    return area_mapping.get(group_name, "core")
