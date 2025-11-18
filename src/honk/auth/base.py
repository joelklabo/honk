"""Base models and enums for auth subsystem."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AuthStatus(str, Enum):
    """Authentication status."""
    VALID = "valid"
    EXPIRED = "expired"
    MISSING = "missing"
    INVALID = "invalid"


class TokenMetadata(BaseModel):
    """Metadata for stored authentication tokens."""
    
    provider: str
    hostname: str
    user: str
    scopes: list[str] = Field(default_factory=list)
    expires_at: Optional[str] = None
    minted_at: Optional[str] = None
    source: str = "unknown"


class AuthResult(BaseModel):
    """Result from authentication operation."""
    
    success: bool
    status: AuthStatus
    message: str
    metadata: Optional[TokenMetadata] = None
    next_steps: list[str] = Field(default_factory=list)
