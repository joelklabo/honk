"""Doctor pack base classes."""
from typing import Protocol, Literal
from pydantic import BaseModel, Field


class PackCheck(BaseModel):
    """A single check within a doctor pack."""
    name: str
    passed: bool
    message: str
    remedy: str | None = None


class PackResult(BaseModel):
    """Result from running a doctor pack."""
    pack: str
    status: Literal["ok", "failed", "skipped"]
    duration_ms: int
    summary: str
    checks: list[PackCheck] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list, description="Remediation commands")


class DoctorPack(Protocol):
    """Protocol for doctor packs."""
    
    name: str
    requires: list[str]
    
    def run(self, plan: bool = False) -> PackResult:
        """Run the pack checks.
        
        Args:
            plan: If True, run in plan mode (no mutations)
            
        Returns:
            PackResult with check results
        """
        ...
