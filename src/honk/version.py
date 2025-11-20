"""Version and build information for honk."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

__version__ = "0.1.0"

def get_git_commit() -> Optional[str]:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_commit_date() -> Optional[str]:
    """Get current git commit date."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            timeout=2
        )
        if result.returncode == 0:
            date_str = result.stdout.strip()
            # Parse and format as ISO date
            dt = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return None


def get_version_info() -> dict:
    """Get complete version information."""
    commit = get_git_commit()
    commit_date = get_git_commit_date()
    
    info = {
        "version": __version__,
        "commit": commit or "unknown",
        "commit_date": commit_date or "unknown",
    }
    
    return info


def format_version_banner() -> str:
    """Format version info as a banner string."""
    info = get_version_info()
    
    parts = [f"honk v{info['version']}"]
    
    if info["commit"] != "unknown":
        parts.append(f"({info['commit']})")
    
    if info["commit_date"] != "unknown":
        parts.append(f"built {info['commit_date']}")
    
    return " ".join(parts)
