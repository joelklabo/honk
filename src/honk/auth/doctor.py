"""Doctor packs for authentication prerequisite checking."""

import time
from typing import Optional
from ..internal.doctor import PackCheck, PackResult
from .providers.github import GitHubAuthProvider
from .providers.azure import AzureAuthProvider
from .base import AuthStatus


def create_github_auth_pack(
    scopes: Optional[list[str]] = None,
    hostname: Optional[str] = None
):
    """Create a doctor pack for GitHub authentication.
    
    Args:
        scopes: Required OAuth scopes
        hostname: GitHub hostname (default: github.com)
        
    Returns:
        DoctorPack instance for GitHub auth checking
    """
    pack_name = "auth-gh"
    if scopes:
        pack_name += f"[{','.join(scopes)}]"
    if hostname and hostname != "github.com":
        pack_name += f"@{hostname}"
    
    class GitHubAuthPack:
        """GitHub authentication doctor pack."""
        
        name = pack_name
        requires: list[str] = []
        
        def run(self, plan: bool = False) -> PackResult:
            """Run GitHub authentication checks."""
            start = time.time()
            provider = GitHubAuthProvider()
            result = provider.status(hostname=hostname)
            
            checks = []
            
            # Check if gh CLI is installed
            if result.status == AuthStatus.MISSING and "not installed" in result.message.lower():
                checks.append(PackCheck(
                    name="gh CLI installed",
                    passed=False,
                    message="gh CLI not found",
                    remedy="Install with: brew install gh"
                ))
            # Check if authenticated
            elif result.status == AuthStatus.MISSING:
                checks.append(PackCheck(
                    name="GitHub authentication",
                    passed=False,
                    message=result.message,
                    remedy="Run: honk auth gh login" + (f" --hostname {hostname}" if hostname else "")
                ))
            else:
                # Authentication successful
                checks.append(PackCheck(
                    name="GitHub authentication",
                    passed=True,
                    message=f"Authenticated as {result.metadata.user if result.metadata else 'unknown'}",
                    remedy=None
                ))
                
                # Check scopes if specified
                if scopes and result.metadata:
                    current_scopes = set(result.metadata.scopes)
                    required_scopes = set(scopes)
                    missing_scopes = required_scopes - current_scopes
                    
                    if missing_scopes:
                        checks.append(PackCheck(
                            name="GitHub scopes",
                            passed=False,
                            message=f"Missing scopes: {', '.join(missing_scopes)}",
                            remedy=f"Run: honk auth gh refresh --scopes {','.join(scopes)}"
                        ))
                    else:
                        checks.append(PackCheck(
                            name="GitHub scopes",
                            passed=True,
                            message=f"Required scopes present: {', '.join(scopes)}",
                            remedy=None
                        ))
            
            duration_ms = int((time.time() - start) * 1000)
            all_passed = all(check.passed for check in checks)
            status: str = "ok" if all_passed else "failed"
            
            summary_parts = []
            if all_passed:
                summary_parts.append("GitHub authentication OK")
            else:
                failed = [c for c in checks if not c.passed]
                summary_parts.append(f"{len(failed)} check(s) failed")
            
            return PackResult(
                pack=self.name,
                status=status,  # type: ignore[arg-type]
                duration_ms=duration_ms,
                summary="; ".join(summary_parts),
                checks=checks,
                next=[c.remedy for c in checks if c.remedy]
            )
    
    return GitHubAuthPack()


def create_azure_auth_pack(org: str):
    """Create a doctor pack for Azure DevOps authentication.
    
    Args:
        org: Azure DevOps organization URL
        
    Returns:
        DoctorPack instance for Azure DevOps auth checking
    """
    pack_name = f"auth-az[{org.split('/')[-1]}]"
    
    class AzureAuthPack:
        """Azure DevOps authentication doctor pack."""
        
        name = pack_name
        requires: list[str] = []
        
        def run(self, plan: bool = False) -> PackResult:
            """Run Azure DevOps authentication checks."""
            start = time.time()
            provider = AzureAuthProvider()
            result = provider.status(org=org)
            
            checks = []
            
            # Check if az CLI is installed
            if result.status == AuthStatus.MISSING and "not installed" in result.message.lower():
                checks.append(PackCheck(
                    name="az CLI installed",
                    passed=False,
                    message="az CLI not found",
                    remedy="Install from: https://aka.ms/install-az-cli"
                ))
            # Check if authenticated to Azure
            elif result.status == AuthStatus.MISSING and "Not logged in to Azure" in result.message:
                checks.append(PackCheck(
                    name="Azure authentication",
                    passed=False,
                    message=result.message,
                    remedy="Run: az login"
                ))
            # Check Azure DevOps PAT
            elif result.status == AuthStatus.MISSING:
                checks.append(PackCheck(
                    name="Azure DevOps PAT",
                    passed=False,
                    message=result.message,
                    remedy=f"Run: honk auth az login --org {org}"
                ))
            else:
                # Authentication successful
                checks.append(PackCheck(
                    name="Azure DevOps authentication",
                    passed=True,
                    message=f"Authenticated to {org} as {result.metadata.user if result.metadata else 'unknown'}",
                    remedy=None
                ))
            
            duration_ms = int((time.time() - start) * 1000)
            all_passed = all(check.passed for check in checks)
            status: str = "ok" if all_passed else "failed"
            
            summary_parts = []
            if all_passed:
                summary_parts.append("Azure DevOps authentication OK")
            else:
                failed = [c for c in checks if not c.passed]
                summary_parts.append(f"{len(failed)} check(s) failed")
            
            return PackResult(
                pack=self.name,
                status=status,  # type: ignore[arg-type]
                duration_ms=duration_ms,
                summary="; ".join(summary_parts),
                checks=checks,
                next=[c.remedy for c in checks if c.remedy]
            )
    
    return AzureAuthPack()


__all__ = [
    "create_github_auth_pack",
    "create_azure_auth_pack",
]
