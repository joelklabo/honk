"""PyPI publisher."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional


class PyPIPublisher:
    """Publishes packages to PyPI."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize PyPI publisher.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.dist_dir = self.project_root / "dist"
    
    def publish(
        self,
        artifacts: Optional[List[Path]] = None,
        token: Optional[str] = None,
        repository: str = "pypi",
        dry_run: bool = False
    ) -> None:
        """Publish package to PyPI.
        
        Args:
            artifacts: Specific artifacts to publish (or all in dist/)
            token: PyPI API token (or from PYPI_TOKEN env var)
            repository: PyPI repository (pypi or testpypi)
            dry_run: If True, don't actually publish
            
        Raises:
            RuntimeError: If publish fails
        """
        if artifacts is None:
            if not self.dist_dir.exists():
                raise RuntimeError("No dist/ directory found. Run build first.")
            artifacts = list(self.dist_dir.glob("*"))
        
        if not artifacts:
            raise RuntimeError("No artifacts to publish")
        
        # Get token from parameter or environment
        token = token or os.getenv("PYPI_TOKEN")
        if not token and not dry_run:
            raise RuntimeError("PYPI_TOKEN not set")
        
        if dry_run:
            print(f"[DRY RUN] Would publish {len(artifacts)} artifact(s) to {repository}")
            for artifact in artifacts:
                print(f"  - {artifact.name}")
            return
        
        # Publish using uv
        cmd = ["uv", "publish", "--token", token]
        if repository != "pypi":
            cmd.extend(["--publish-url", f"https://upload.pypi.org/legacy/"])
        
        cmd.extend(str(a) for a in artifacts)
        
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Publish failed: {result.stderr}")
