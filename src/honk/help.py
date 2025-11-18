"""Custom help formatters for machine-readable output."""
import json
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
