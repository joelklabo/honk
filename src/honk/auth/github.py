"""GitHub authentication provider."""

import subprocess
from typing import Optional

from .base import AuthStatus, TokenMetadata, AuthResult


class GitHubAuthProvider:
    """GitHub authentication provider using gh CLI."""
    
    def __init__(self, hostname: str = "github.com"):
        """Initialize GitHub auth provider.
        
        Args:
            hostname: GitHub hostname (github.com or GHE instance)
        """
        self.hostname = hostname
        self.provider = "github"
    
    def status(self, user: Optional[str] = None) -> AuthResult:
        """Check GitHub authentication status.
        
        Args:
            user: Optional specific user to check
            
        Returns:
            AuthResult with current status
        """
        try:
            # Check if gh is installed
            result = subprocess.run(
                ["gh", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="gh CLI not installed",
                    next_steps=["Install gh CLI: brew install gh"]
                )
            
            # Check auth status with JSON output
            cmd = ["gh", "auth", "status", "--hostname", self.hostname]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message=f"Not logged in to {self.hostname}",
                    next_steps=[f"Run: honk auth gh login --hostname {self.hostname}"]
                )
            
            # Parse status output to extract metadata
            # gh auth status doesn't have JSON output, so parse text
            lines = result.stderr.splitlines()
            user_line = next((line for line in lines if "Logged in to" in line), None)
            scopes_line = next((line for line in lines if "Token scopes:" in line), None)
            
            username = None
            if user_line:
                parts = user_line.split("as")
                if len(parts) > 1:
                    username = parts[1].strip().split()[0]
            
            scopes = []
            if scopes_line:
                scopes_str = scopes_line.split(":")[-1].strip()
                scopes = [s.strip() for s in scopes_str.split(",")]
            
            metadata = TokenMetadata(
                provider=self.provider,
                hostname=self.hostname,
                user=username or "unknown",
                scopes=scopes,
                source="gh auth status"
            )
            
            return AuthResult(
                success=True,
                status=AuthStatus.VALID,
                message=f"Authenticated to {self.hostname} as {username}",
                metadata=metadata
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
                message=f"Error checking auth: {e}",
                next_steps=["Try: gh auth status"]
            )
    
    def login(self, scopes: Optional[list[str]] = None, web: bool = True) -> AuthResult:
        """Login to GitHub.
        
        Args:
            scopes: OAuth scopes to request
            web: Use web-based OAuth flow (vs device code)
            
        Returns:
            AuthResult with login status
        """
        try:
            cmd = ["gh", "auth", "login", "--hostname", self.hostname]
            
            if web:
                cmd.append("--web")
            
            if scopes:
                cmd.extend(["--scopes", ",".join(scopes)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for user interaction
            )
            
            if result.returncode == 0:
                # Get updated status
                status_result = self.status()
                return AuthResult(
                    success=True,
                    status=AuthStatus.VALID,
                    message=f"Successfully logged in to {self.hostname}",
                    metadata=status_result.metadata,
                    next_steps=[]
                )
            else:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message=f"Login failed: {result.stderr}",
                    next_steps=["Check your credentials and try again"]
                )
                
        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Login error: {e}",
                next_steps=["Try: gh auth login"]
            )
    
    def refresh(self, scopes: Optional[list[str]] = None) -> AuthResult:
        """Refresh GitHub authentication with new scopes.
        
        Args:
            scopes: New scopes to request
            
        Returns:
            AuthResult with refresh status
        """
        try:
            cmd = ["gh", "auth", "refresh", "--hostname", self.hostname]
            
            if scopes:
                cmd.extend(["--scopes", ",".join(scopes)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                status_result = self.status()
                return AuthResult(
                    success=True,
                    status=AuthStatus.VALID,
                    message=f"Successfully refreshed auth for {self.hostname}",
                    metadata=status_result.metadata,
                    next_steps=[]
                )
            else:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message=f"Refresh failed: {result.stderr}",
                    next_steps=["Try logging in again: honk auth gh login"]
                )
                
        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Refresh error: {e}",
                next_steps=["Try: gh auth refresh"]
            )
    
    def logout(self) -> AuthResult:
        """Logout from GitHub.
        
        Returns:
            AuthResult with logout status
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "logout", "--hostname", self.hostname],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return AuthResult(
                    success=True,
                    status=AuthStatus.MISSING,
                    message=f"Successfully logged out from {self.hostname}",
                    next_steps=[]
                )
            else:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message=f"Logout failed: {result.stderr}",
                    next_steps=[]
                )
                
        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Logout error: {e}",
                next_steps=[]
            )
    
    def ensure(self, scopes: Optional[list[str]] = None) -> AuthResult:
        """Ensure GitHub authentication is valid.
        
        Args:
            scopes: Required scopes
            
        Returns:
            AuthResult with ensure status
        """
        status_result = self.status()
        
        if status_result.success:
            # Check if we have required scopes
            if scopes and status_result.metadata:
                current_scopes = set(status_result.metadata.scopes)
                required_scopes = set(scopes)
                
                if not required_scopes.issubset(current_scopes):
                    # Need to refresh with additional scopes
                    return self.refresh(scopes)
            
            return status_result
        else:
            # Not logged in, need to login
            status_result.next_steps = [
                f"Run: honk auth gh login --hostname {self.hostname}"
            ]
            return status_result
