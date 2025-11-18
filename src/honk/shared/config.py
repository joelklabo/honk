"""Shared configuration management."""

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomli
except ImportError:
    import tomllib as tomli  # Python 3.11+


class Config:
    """Configuration manager for Honk tools."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize config manager.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.pyproject_path = self.project_root / "pyproject.toml"
        self._config: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from pyproject.toml.
        
        Returns:
            Configuration dictionary
        """
        if self._config is not None:
            return self._config
        
        if not self.pyproject_path.exists():
            self._config = {}
            return self._config
        
        with open(self.pyproject_path, "rb") as f:
            data = tomli.load(f)
        
        # Extract honk configuration
        self._config = data.get("tool", {}).get("honk", {})
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (dot-notation supported)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        config = self.load()
        
        # Handle dot notation: "release.ai_enabled"
        keys = key.split(".")
        value = config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def get_release_config(self) -> Dict[str, Any]:
        """Get release tool configuration.
        
        Returns:
            Release configuration dictionary
        """
        return self.get("release", {})
