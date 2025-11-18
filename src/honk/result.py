"""Result envelope for honk CLI commands."""
from typing import Any, Literal
from pydantic import BaseModel, Field


class Link(BaseModel):
    """Link to related resources."""
    rel: str
    href: str


class NextStep(BaseModel):
    """Suggested next command to run."""
    run: list[str]
    summary: str


class PackResult(BaseModel):
    """Result from a doctor pack check."""
    pack: str
    status: Literal["ok", "failed", "skipped"]
    duration_ms: int


class ResultEnvelope(BaseModel):
    """Standard result envelope for all honk commands."""
    version: str = Field(default="1.0")
    command: list[str]
    status: str
    changed: bool = False
    code: str
    summary: str
    run_id: str
    duration_ms: int
    facts: dict[str, Any] = Field(default_factory=dict)
    pack_results: list[PackResult] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    next: list[NextStep] = Field(default_factory=list)
    retry_after_secs: int = 0


# Exit codes
EXIT_OK = 0
EXIT_PREREQ_FAILED = 10
EXIT_NEEDS_AUTH = 11
EXIT_TOKEN_EXPIRED = 12
EXIT_NETWORK = 20
EXIT_SYSTEM = 30
EXIT_BUG = 50
EXIT_RATE_LIMITED = 60
