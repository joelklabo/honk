"""Custom help formatters for machine-readable output."""

from typing import Any
from pydantic import BaseModel, Field


class ArgumentSchema(BaseModel):
    """Schema for a command argument."""

    name: str
    type: str
    required: bool = True
    default: Any = None
    help: str = ""


class OptionSchema(BaseModel):
    """Schema for a command option."""

    names: list[str]
    type: str
    required: bool = False
    default: Any = None
    help: str = ""


class ExampleSchema(BaseModel):
    """Example command invocation."""

    command: str
    description: str


class CommandHelpSchema(BaseModel):
    """Machine-readable help schema for a command."""

    version: str = Field(default="1.0")
    command: list[str]
    description: str
    arguments: list[ArgumentSchema] = Field(default_factory=list)
    options: list[OptionSchema] = Field(default_factory=list)
    examples: list[ExampleSchema] = Field(default_factory=list)
    doctor_packs: list[str] = Field(default_factory=list)
    auth_scopes: dict[str, list[str]] = Field(default_factory=dict)


def emit_help_json(schema: CommandHelpSchema) -> str:
    """Emit help schema as JSON."""
    return schema.model_dump_json(indent=2)


def get_command_help_from_registry(command_path: list[str]) -> CommandHelpSchema | None:
    """Get help schema for a command from the registry."""
    from . import registry

    all_commands = registry.get_all_commands()
    for cmd in all_commands:
        if cmd.full_path == command_path:
            return CommandHelpSchema(
                command=cmd.full_path,
                description=cmd.description,
                arguments=[
                    ArgumentSchema(
                        name=arg.name,
                        type=arg.type_hint,
                        required=arg.required,
                        default=arg.default,
                        help=arg.help,
                    )
                    for arg in cmd.arguments
                ],
                options=[
                    OptionSchema(
                        names=opt.names,
                        type=opt.type_hint,
                        required=opt.required,
                        default=opt.default,
                        help=opt.help,
                    )
                    for opt in cmd.options
                ],
                examples=[
                    ExampleSchema(command=ex.command, description=ex.description)
                    for ex in cmd.examples
                ],
                doctor_packs=cmd.prereqs,
                auth_scopes=cmd.auth_scopes,
            )
    return None
