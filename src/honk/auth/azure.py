"""Azure DevOps authentication provider."""

import json
import subprocess
from typing import Optional

from .base import AuthStatus, TokenMetadata, AuthResult


class AzureDevOpsAuthProvider:
    """Azure DevOps authentication provider using az CLI."""
    
    def __init__(self, org: Optional[str] = None):
        """Initialize Azure DevOps auth provider.
        
        Args:
            org: Azure DevOps organization URL
        """
        self.org = org
        self.provider = "azure_devops"
    
    def status(self) -> AuthResult:
        """Check Azure DevOps authentication status.
            
        Returns:
            AuthResult with current status
        """
        try:
            # Check if az is installed
            result = subprocess.run(
                ["az", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="az CLI not installed",
                    next_steps=["Install az CLI: https://aka.ms/install-az-cli"]
                )
            
            # Check if logged in
            result = subprocess.run(
                ["az", "account", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="Not logged in to Azure",
                    next_steps=["Run: honk auth az login"]
                )
            
            # Parse account info
            try:
                account_info = json.loads(result.stdout)
                user = account_info.get("user", {}).get("name", "unknown")
                
                metadata = TokenMetadata(
                    provider=self.provider,
                    hostname="dev.azure.com",
                    user=user,
                    source="az account show"
                )
                
                return AuthResult(
                    success=True,
                    status=AuthStatus.VALID,
                    message=f"Authenticated to Azure as {user}",
                    metadata=metadata
                )
            except json.JSONDecodeError:
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message="Failed to parse Azure account info",
                    next_steps=["Try: az login"]
                )
            
        except FileNotFoundError:
            return AuthResult(
                success=False,
                status=AuthStatus.MISSING,
                message="az CLI not found",
                next_steps=["Install az CLI: https://aka.ms/install-az-cli"]
            )
        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Error checking auth: {e}",
                next_steps=["Try: az account show"]
            )
    
    def login(self) -> AuthResult:
        """Login to Azure.
            
        Returns:
            AuthResult with login status
        """
        try:
            # Use device code flow for headless compatibility
            result = subprocess.run(
                ["az", "login", "--use-device-code"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for user interaction
            )
            
            if result.returncode == 0:
                status_result = self.status()
                return AuthResult(
                    success=True,
                    status=AuthStatus.VALID,
                    message="Successfully logged in to Azure",
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
                next_steps=["Try: az login"]
            )
    
    def logout(self) -> AuthResult:
        """Logout from Azure.
            
        Returns:
            AuthResult with logout status
        """
        try:
            result = subprocess.run(
                ["az", "logout"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return AuthResult(
                    success=True,
                    status=AuthStatus.MISSING,
                    message="Successfully logged out from Azure",
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
    
    def ensure(self) -> AuthResult:
        """Ensure Azure authentication is valid.
            
        Returns:
            AuthResult with ensure status
        """
        status_result = self.status()
        
        if not status_result.success:
            status_result.next_steps = ["Run: honk auth az login"]
        
        return status_result
