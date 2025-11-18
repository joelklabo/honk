"""Provider implementations for authentication."""

from ..providers_legacy import ensure_gh_auth, ensure_az_auth
from .github import GitHubAuthProvider
from .azure import AzureAuthProvider

__all__ = [
    "ensure_gh_auth",
    "ensure_az_auth",
    "GitHubAuthProvider",
    "AzureAuthProvider",
]
