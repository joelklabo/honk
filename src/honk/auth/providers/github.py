"""GitHub authentication provider."""

import subprocess
from typing import Optional

from ..base import AuthStatus, TokenMetadata, AuthResult
from ..keyring_store import KeyringStore


class GitHubAuthProvider:
    """Provider for GitHub authentication via gh CLI."""

    def __init__(self):
        self.store = KeyringStore()
        self.default_hostname = "github.com"

    def status(self, hostname: Optional[str] = None) -> AuthResult:
        """Check GitHub authentication status.
        
        Args:
            hostname: GitHub hostname (default: github.com)
            
        Returns:
            AuthResult with status and metadata
        """
        hostname = hostname or self.default_hostname
        
        try:
            # Check if gh CLI is available
            version_result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if version_result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="gh CLI not installed",
                    next_steps=["Install gh CLI: brew install gh"]
                )

            # Check auth status via gh auth status
            status_result = subprocess.run(
                ["gh", "auth", "status", "--hostname", hostname],
                capture_output=True,
                text=True,
                timeout=10
            )

            if status_result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message=f"Not logged into {hostname}",
                    next_steps=[f"honk auth gh login --hostname {hostname}"]
                )

            # Get detailed status in JSON format
            subprocess.run(
                ["gh", "auth", "status", "--hostname", hostname, "--show-token"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse status output (gh auth status doesn't always have JSON, parse text)
            user = None
            scopes = []
            
            for line in status_result.stdout.split("\n"):
                if "Logged in to" in line and "as" in line:
                    parts = line.split("as")
                    if len(parts) > 1:
                        user = parts[1].strip().split()[0]
                elif "Token scopes:" in line:
                    scope_part = line.split(":")
                    if len(scope_part) > 1:
                        scopes = [s.strip() for s in scope_part[1].split(",")]

            if not user:
                user = "unknown"

            # Create metadata
            metadata = TokenMetadata(
                provider="github",
                hostname=hostname,
                user=user,
                scopes=scopes,
                source="gh auth status"
            )

            # Check for expiry warnings (GitHub tokens typically don't expire unless PAT)

            # Store metadata
            key = f"github/{hostname}/{user}"
            self.store.store_metadata(key, metadata)

            return AuthResult(
                success=True,
                status=AuthStatus.VALID,
                message=f"Authenticated as {user} on {hostname}",
                metadata=metadata,
                next_steps=[]
            )

        except subprocess.TimeoutExpired:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="gh CLI timed out",
                next_steps=["Check gh CLI installation"]
            )
        except FileNotFoundError:
            return AuthResult(
                success=False,
                status=AuthStatus.MISSING,
                message="gh CLI not found",
                next_steps=["Install gh CLI: brew install gh"]
            )
        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Error checking status: {str(e)}",
                next_steps=["Run: gh auth status"]
            )

    def login(
        self,
        hostname: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        web: bool = True
    ) -> AuthResult:
        """Login to GitHub.
        
        Args:
            hostname: GitHub hostname (default: github.com)
            scopes: OAuth scopes to request
            web: Use web-based auth flow (default: True)
            
        Returns:
            AuthResult with login status
        """
        hostname = hostname or self.default_hostname
        scopes = scopes or ["repo", "read:org", "gist"]

        try:
            # Build gh auth login command
            cmd = ["gh", "auth", "login", "--hostname", hostname]
            
            if web:
                cmd.append("--web")
            
            if scopes:
                cmd.extend(["--scopes", ",".join(scopes)])

            # Run login
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                # Get updated status
                status_result = self.status(hostname)
                return AuthResult(
                    success=True,
                    status=AuthStatus.VALID,
                    message=f"Successfully logged in to {hostname}",
                    metadata=status_result.metadata,
                    next_steps=[]
                )
            else:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message=f"Login failed: {result.stderr}",
                    next_steps=["Try again: honk auth gh login"]
                )

        except subprocess.TimeoutExpired:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="Login timed out",
                next_steps=["Try again with shorter timeout"]
            )
        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Login error: {str(e)}",
                next_steps=["Run: gh auth login"]
            )

    def refresh(
        self,
        hostname: Optional[str] = None,
        scopes: Optional[list[str]] = None
    ) -> AuthResult:
        """Refresh GitHub authentication and update scopes.
        
        Args:
            hostname: GitHub hostname (default: github.com)
            scopes: New or additional scopes to request
            
        Returns:
            AuthResult with refresh status
        """
        hostname = hostname or self.default_hostname

        try:
            # Check current status first
            current_status = self.status(hostname)
            if current_status.status == AuthStatus.MISSING:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="Not logged in, cannot refresh",
                    next_steps=[f"honk auth gh login --hostname {hostname}"]
                )

            # Build refresh command
            cmd = ["gh", "auth", "refresh", "--hostname", hostname]
            
            if scopes:
                cmd.extend(["--scopes", ",".join(scopes)])

            # Run refresh
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Get updated status
                status_result = self.status(hostname)
                return AuthResult(
                    success=True,
                    status=AuthStatus.VALID,
                    message=f"Successfully refreshed authentication for {hostname}",
                    metadata=status_result.metadata,
                    next_steps=[]
                )
            else:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message=f"Refresh failed: {result.stderr}",
                    next_steps=[f"honk auth gh login --hostname {hostname}"]
                )

        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Refresh error: {str(e)}",
                next_steps=["Run: gh auth refresh"]
            )

    def logout(self, hostname: Optional[str] = None) -> AuthResult:
        """Logout from GitHub.
        
        Args:
            hostname: GitHub hostname (default: github.com)
            
        Returns:
            AuthResult with logout status
        """
        hostname = hostname or self.default_hostname

        try:
            # Run logout
            result = subprocess.run(
                ["gh", "auth", "logout", "--hostname", hostname],
                capture_output=True,
                text=True,
                timeout=10,
                input="y\n"  # Confirm logout
            )

            if result.returncode == 0:
                # Clean up stored metadata
                status_result = self.status(hostname)
                if status_result.metadata:
                    key = f"github/{hostname}/{status_result.metadata.user}"
                    try:
                        self.store.delete_token(key)
                    except Exception:
                        pass  # Token may not exist in keyring

                return AuthResult(
                    success=True,
                    status=AuthStatus.MISSING,
                    message=f"Successfully logged out from {hostname}",
                    next_steps=[]
                )
            else:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message=f"Logout failed: {result.stderr}",
                    next_steps=["Run: gh auth logout"]
                )

        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Logout error: {str(e)}",
                next_steps=["Run: gh auth logout"]
            )
