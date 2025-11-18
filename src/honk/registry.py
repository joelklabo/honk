"""Command registry for introspection."""

from typing import Any
from pydantic import BaseModel, Field


class CommandArgument(BaseModel):
    """Metadata for a command argument."""

    name: str
    type_hint: str
    required: bool = True
    default: Any = None
    help: str = ""


class CommandOption(BaseModel):
    """Metadata for a command option."""

    names: list[str]
    type_hint: str
    required: bool = False
    default: Any = None
    help: str = ""


class CommandExample(BaseModel):
    """Example command usage."""

    command: str
    description: str


class CommandMetadata(BaseModel):
    """Metadata for a single command."""

    area: str
    tool: str
    action: str
    full_path: list[str]
    description: str
    arguments: list[CommandArgument] = Field(default_factory=list)
    options: list[CommandOption] = Field(default_factory=list)
    examples: list[CommandExample] = Field(default_factory=list)
    prereqs: list[str] = Field(default_factory=list)
    auth_scopes: dict[str, list[str]] = Field(default_factory=dict)


class IntrospectionSchema(BaseModel):
    """Full introspection schema for all commands."""

    version: str = Field(default="1.0")
    commands: list[CommandMetadata]


# Command registry (will be populated by decorators)
_command_registry: list[CommandMetadata] = []


def register_command(metadata: CommandMetadata) -> None:
    """Register a command in the global registry."""
    _command_registry.append(metadata)


def get_all_commands() -> list[CommandMetadata]:
    """Get all registered commands."""
    return _command_registry.copy()


def get_introspection_schema() -> IntrospectionSchema:
    """Get the full introspection schema."""
    return IntrospectionSchema(commands=get_all_commands())
