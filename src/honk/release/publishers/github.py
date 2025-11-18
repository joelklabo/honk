"""GitHub Releases publisher."""

import subprocess
from pathlib import Path
from typing import List, Optional


class GitHubPublisher:
    """Creates GitHub releases."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize GitHub publisher.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
    
    def create_release(
        self,
        version: str,
        changelog: str,
        artifacts: Optional[List[Path]] = None,
        draft: bool = False,
        prerelease: bool = False,
        dry_run: bool = False
    ) -> None:
        """Create GitHub release.
        
        Args:
            version: Version number (without 'v' prefix)
            changelog: Release notes
            artifacts: Files to attach to release
            draft: Create as draft
            prerelease: Mark as prerelease
            dry_run: Don't actually create release
            
        Raises:
            RuntimeError: If release creation fails
        """
        tag = f"v{version}"
        
        if dry_run:
            print(f"[DRY RUN] Would create GitHub release {tag}")
            if artifacts:
                print(f"  With {len(artifacts)} artifact(s)")
            return
        
        # Build gh CLI command
        cmd = ["gh", "release", "create", tag]
        
        if draft:
            cmd.append("--draft")
        if prerelease:
            cmd.append("--prerelease")
        
        # Add release notes
        cmd.extend(["--title", f"Release {version}"])
        cmd.extend(["--notes", changelog])
        
        # Add artifacts
        if artifacts:
            cmd.extend(str(a) for a in artifacts)
        
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"GitHub release failed: {result.stderr}")
