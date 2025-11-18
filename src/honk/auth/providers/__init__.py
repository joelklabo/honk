"""Provider implementations for authentication."""

from ..providers_legacy import ensure_gh_auth, ensure_az_auth

__all__ = ["ensure_gh_auth", "ensure_az_auth"]
