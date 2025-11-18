"""Auth provider implementations."""
import subprocess
import sys


def ensure_gh_auth(scopes: list[str] | None = None) -> tuple[bool, str]:
    """Ensure GitHub authentication via gh CLI.
    
    Args:
        scopes: Optional list of required OAuth scopes
        
    Returns:
        Tuple of (success: bool, message: str)
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
            return False, "gh CLI not installed. Install with: brew install gh"
        
        # Check auth status
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "GitHub auth: OK"
        else:
            return False, "Not logged in. Run: gh auth login"
            
    except FileNotFoundError:
        return False, "gh CLI not found"
    except Exception as e:
        return False, f"Error checking gh auth: {e}"


def ensure_az_auth(org: str | None = None) -> tuple[bool, str]:
    """Ensure Azure DevOps authentication via az CLI.
    
    Args:
        org: Optional organization URL
        
    Returns:
        Tuple of (success: bool, message: str)
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
            return False, "az CLI not installed. Install from: https://aka.ms/install-az-cli"
        
        # Check if logged in
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "Azure auth: OK"
        else:
            return False, "Not logged in. Run: az login"
            
    except FileNotFoundError:
        return False, "az CLI not found"
    except Exception as e:
        return False, f"Error checking az auth: {e}"
