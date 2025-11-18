"""Authentication subsystem for honk."""

from .providers import ensure_gh_auth, ensure_az_auth

__all__ = ["ensure_gh_auth", "ensure_az_auth"]
