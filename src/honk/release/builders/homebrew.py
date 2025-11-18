"""Homebrew formula generator."""

from pathlib import Path
from typing import Optional


class HomebrewBuilder:
    """Generates Homebrew formulae."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize Homebrew builder.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
    
    def generate_formula(
        self,
        version: str,
        description: str,
        homepage: str,
        tarball_url: str,
        sha256: str
    ) -> str:
        """Generate Homebrew formula.
        
        Args:
            version: Version number
            description: Package description
            homepage: Project homepage
            tarball_url: URL to source tarball
            sha256: SHA256 of tarball
            
        Returns:
            Formula content as string
        """
        formula = f'''class Honk < Formula
  include Language::Python::Virtualenv

  desc "{description}"
  homepage "{homepage}"
  url "{tarball_url}"
  sha256 "{sha256}"
  
  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/honk", "--version"
  end
end
'''
        return formula
    
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        import hashlib
        
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
