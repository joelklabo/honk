"""Azure DevOps authentication provider."""

import json
import subprocess
from typing import Optional

from ..base import AuthStatus, TokenMetadata, AuthResult
from ..keyring_store import KeyringStore


class AzureAuthProvider:
    """Provider for Azure DevOps authentication via az CLI."""

    def __init__(self):
        self.store = KeyringStore()

    def status(self, org: Optional[str] = None) -> AuthResult:
        """Check Azure DevOps authentication status.
        
        Args:
            org: Azure DevOps organization URL
            
        Returns:
            AuthResult with status and metadata
        """
        if not org:
            return AuthResult(
                success=False,
                status=AuthStatus.MISSING,
                message="Organization URL required",
                next_steps=["honk auth az status --org <url>"]
            )

        try:
            # Check if az CLI is available
            version_result = subprocess.run(
                ["az", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if version_result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="az CLI not installed",
                    next_steps=["Install az CLI from: https://aka.ms/install-az-cli"]
                )

            # Check if logged into Azure
            account_result = subprocess.run(
                ["az", "account", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if account_result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="Not logged into Azure",
                    next_steps=["az login"]
                )

            # Parse account info
            try:
                account_info = json.loads(account_result.stdout)
                user = account_info.get("user", {}).get("name", "unknown")
            except json.JSONDecodeError:
                user = "unknown"

            # Check Azure DevOps PAT by attempting to list projects
            # This uses either AZURE_DEVOPS_EXT_PAT env var or stored PAT
            project_result = subprocess.run(
                ["az", "devops", "project", "list", "--organization", org],
                capture_output=True,
                text=True,
                timeout=15
            )

            if project_result.returncode != 0:
                # Check if it's a PAT issue
                if "PAT" in project_result.stderr or "token" in project_result.stderr.lower():
                    return AuthResult(
                        success=False,
                        status=AuthStatus.MISSING,
                        message=f"No valid PAT for {org}",
                        next_steps=[f"honk auth az login --org {org}"]
                    )
                return AuthResult(
                    success=False,
                    status=AuthStatus.INVALID,
                    message=f"Cannot access {org}: {project_result.stderr}",
                    next_steps=[f"honk auth az login --org {org}"]
                )

            # Create metadata
            metadata = TokenMetadata(
                provider="azure_devops",
                hostname=org,
                user=user,
                scopes=["vso.code", "vso.work"],  # Common scopes
                source="az devops"
            )

            # Store metadata
            key = f"azure_devops/{org}/{user}"
            self.store.store_metadata(key, metadata)

            return AuthResult(
                success=True,
                status=AuthStatus.VALID,
                message=f"Authenticated to {org} as {user}",
                metadata=metadata,
                next_steps=[]
            )

        except subprocess.TimeoutExpired:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message="az CLI timed out",
                next_steps=["Check az CLI installation"]
            )
        except FileNotFoundError:
            return AuthResult(
                success=False,
                status=AuthStatus.MISSING,
                message="az CLI not found",
                next_steps=["Install az CLI from: https://aka.ms/install-az-cli"]
            )
        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Error checking status: {str(e)}",
                next_steps=["Run: az devops project list"]
            )

    def login(self, org: Optional[str] = None) -> AuthResult:
        """Login to Azure DevOps.
        
        Args:
            org: Azure DevOps organization URL
            
        Returns:
            AuthResult with login status
        """
        if not org:
            return AuthResult(
                success=False,
                status=AuthStatus.MISSING,
                message="Organization URL required",
                next_steps=["honk auth az login --org <url>"]
            )

        try:
            # First ensure Azure login
            account_result = subprocess.run(
                ["az", "account", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if account_result.returncode != 0:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message="Not logged into Azure. Please run 'az login' first",
                    next_steps=["az login", f"honk auth az login --org {org}"]
                )

            # Run az devops login
            result = subprocess.run(
                ["az", "devops", "login", "--organization", org],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Get updated status
                status_result = self.status(org)
                return AuthResult(
                    success=True,
                    status=AuthStatus.VALID,
                    message=f"Successfully logged into {org}",
                    metadata=status_result.metadata,
                    next_steps=[]
                )
            else:
                return AuthResult(
                    success=False,
                    status=AuthStatus.MISSING,
                    message=f"Login failed: {result.stderr}",
                    next_steps=[
                        f"Create PAT at https://dev.azure.com/{org.split('/')[-1]}/_usersSettings/tokens",
                        "Then run: az devops login --organization <org>"
                    ]
                )

        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Login error: {str(e)}",
                next_steps=["Run: az devops login"]
            )

    def refresh(self, org: Optional[str] = None) -> AuthResult:
        """Refresh Azure DevOps authentication.
        
        Note: Azure DevOps PATs cannot be extended. This command
        provides guidance on creating a new PAT.
        
        Args:
            org: Azure DevOps organization URL
            
        Returns:
            AuthResult with refresh guidance
        """
        if not org:
            return AuthResult(
                success=False,
                status=AuthStatus.MISSING,
                message="Organization URL required",
                next_steps=["honk auth az refresh --org <url>"]
            )

        # Azure PATs cannot be refreshed/extended, only recreated
        org_name = org.split("/")[-1]
        
        return AuthResult(
            success=True,
            status=AuthStatus.VALID,
            message="Azure DevOps PATs cannot be extended automatically",
            next_steps=[
                f"Create new PAT at: https://dev.azure.com/{org_name}/_usersSettings/tokens",
                f"Then run: honk auth az login --org {org}",
                "Consider setting longer expiration (90 days) or using service principals for automation"
            ]
        )

    def logout(self, org: Optional[str] = None) -> AuthResult:
        """Logout from Azure DevOps.
        
        Args:
            org: Azure DevOps organization URL
            
        Returns:
            AuthResult with logout status
        """
        if not org:
            return AuthResult(
                success=False,
                status=AuthStatus.MISSING,
                message="Organization URL required",
                next_steps=["honk auth az logout --org <url>"]
            )

        try:
            # Clear stored PAT from environment/config
            # The az CLI doesn't have a logout command, so we clean up our metadata
            
            # Get current user
            account_result = subprocess.run(
                ["az", "account", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            user = "unknown"
            if account_result.returncode == 0:
                try:
                    account_info = json.loads(account_result.stdout)
                    user = account_info.get("user", {}).get("name", "unknown")
                except Exception:
                    pass

            # Clear stored metadata and keyring entry
            key = f"azure_devops/{org}/{user}"
            try:
                self.store.delete_token(key)
            except Exception:
                pass  # Token may not exist

            return AuthResult(
                success=True,
                status=AuthStatus.MISSING,
                message=f"Cleared authentication for {org}",
                next_steps=[
                    "Note: Azure login (az login) is still active",
                    "To fully log out: az logout",
                    f"To revoke PAT: https://dev.azure.com/{org.split('/')[-1]}/_usersSettings/tokens"
                ]
            )

        except Exception as e:
            return AuthResult(
                success=False,
                status=AuthStatus.INVALID,
                message=f"Logout error: {str(e)}",
                next_steps=["Run: az logout"]
            )
