"""PyPI package builder."""

import subprocess
from pathlib import Path
from typing import List, Optional


class PyPIBuilder:
    """Builds Python packages for PyPI distribution."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize PyPI builder.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.dist_dir = self.project_root / "dist"
    
    def clean(self) -> None:
        """Clean previous build artifacts."""
        if self.dist_dir.exists():
            import shutil
            shutil.rmtree(self.dist_dir)
    
    def build(self, clean_first: bool = True) -> List[Path]:
        """Build package using uv.
        
        Args:
            clean_first: Clean dist directory before building
            
        Returns:
            List of built artifact paths
            
        Raises:
            RuntimeError: If build fails
        """
        if clean_first:
            self.clean()
        
        # Build with uv
        result = subprocess.run(
            ["uv", "build"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Build failed: {result.stderr}")
        
        # Return list of built artifacts
        if not self.dist_dir.exists():
            return []
        
        return list(self.dist_dir.glob("*"))
    
    def get_artifacts(self) -> List[Path]:
        """Get list of built artifacts.
        
        Returns:
            List of artifact paths in dist/
        """
        if not self.dist_dir.exists():
            return []
        
        return list(self.dist_dir.glob("*"))
