"""Semantic version bumper."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from honk.release.analyzer import ReleaseType


@dataclass
class Version:
    """Semantic version."""
    
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    @classmethod
    def parse(cls, version_string: str) -> "Version":
        """Parse version string into Version object.
        
        Args:
            version_string: Version string (e.g., "1.2.3", "v1.2.3-beta.1+build.123")
            
        Returns:
            Version object
            
        Raises:
            ValueError: If version string is invalid
        """
        # Remove 'v' prefix if present
        if version_string.startswith('v'):
            version_string = version_string[1:]
        
        # Parse with regex
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-\.]+))?(?:\+([0-9A-Za-z-\.]+))?$'
        match = re.match(pattern, version_string)
        
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        
        major, minor, patch, prerelease, build = match.groups()
        
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build
        )
    
    def bump(self, release_type: ReleaseType) -> "Version":
        """Bump version based on release type.
        
        Args:
            release_type: Type of release (MAJOR, MINOR, PATCH)
            
        Returns:
            New Version with bumped number
        """
        if release_type == ReleaseType.MAJOR:
            return Version(
                major=self.major + 1,
                minor=0,
                patch=0
            )
        elif release_type == ReleaseType.MINOR:
            return Version(
                major=self.major,
                minor=self.minor + 1,
                patch=0
            )
        elif release_type == ReleaseType.PATCH:
            return Version(
                major=self.major,
                minor=self.minor,
                patch=self.patch + 1
            )
        else:
            raise ValueError(f"Unknown release type: {release_type}")
    
    def __str__(self) -> str:
        """Convert to string representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        
        if self.prerelease:
            version += f"-{self.prerelease}"
        
        if self.build:
            version += f"+{self.build}"
        
        return version
    
    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, Version):
            return False
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease and
            self.build == other.build
        )


class VersionBumper:
    """Handles version bumping in project files."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize version bumper.
        
        Args:
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
    
    def get_current_version(self) -> Version:
        """Get current version from pyproject.toml.
        
        Returns:
            Current Version
            
        Raises:
            FileNotFoundError: If pyproject.toml not found
            ValueError: If version not found or invalid
        """
        pyproject_path = self.project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
        
        content = pyproject_path.read_text()
        
        # Find version line
        pattern = r'version\s*=\s*"([^"]+)"'
        match = re.search(pattern, content)
        
        if not match:
            raise ValueError("Version not found in pyproject.toml")
        
        return Version.parse(match.group(1))
    
    def bump_version(
        self,
        release_type: ReleaseType,
        dry_run: bool = False
    ) -> tuple[Version, Version]:
        """Bump version in project files.
        
        Args:
            release_type: Type of release (MAJOR, MINOR, PATCH)
            dry_run: If True, don't modify files
            
        Returns:
            Tuple of (old_version, new_version)
        """
        old_version = self.get_current_version()
        new_version = old_version.bump(release_type)
        
        if not dry_run:
            self._update_files(old_version, new_version)
        
        return (old_version, new_version)
    
    def _update_files(self, old_version: Version, new_version: Version) -> None:
        """Update version in all project files.
        
        Args:
            old_version: Current version
            new_version: New version
        """
        files_to_update = [
            self.project_root / "pyproject.toml",
            self.project_root / "src" / "honk" / "__init__.py",
        ]
        
        old_str = str(old_version)
        new_str = str(new_version)
        
        for file_path in files_to_update:
            if not file_path.exists():
                continue
            
            content = file_path.read_text()
            
            # Update version string
            if "pyproject.toml" in str(file_path):
                # Update TOML format: version = "x.y.z"
                content = re.sub(
                    r'version\s*=\s*"[^"]+"',
                    f'version = "{new_str}"',
                    content
                )
            else:
                # Update Python format: __version__ = "x.y.z"
                content = re.sub(
                    r'__version__\s*=\s*"[^"]+"',
                    f'__version__ = "{new_str}"',
                    content
                )
            
            file_path.write_text(content)
    
    def get_version_files(self) -> List[Path]:
        """Get list of files that contain version strings.
        
        Returns:
            List of file paths
        """
        return [
            self.project_root / "pyproject.toml",
            self.project_root / "src" / "honk" / "__init__.py",
        ]
