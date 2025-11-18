"""Unit tests for shared config."""

import pytest
from pathlib import Path

from honk.shared.config import Config


class TestConfig:
    """Tests for configuration manager."""
    
    @pytest.fixture
    def config_file(self, tmp_path):
        """Create test pyproject.toml."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.honk]
version = "1.0.0"

[tool.honk.release]
ai_enabled = true
auto_push = false
changelog_file = "CHANGELOG.md"
        """)
        return tmp_path
    
    def test_load_config(self, config_file):
        """Test loading configuration."""
        config = Config(project_root=config_file)
        data = config.load()
        
        assert data["version"] == "1.0.0"
        assert "release" in data
    
    def test_get_simple_key(self, config_file):
        """Test getting simple key."""
        config = Config(project_root=config_file)
        
        assert config.get("version") == "1.0.0"
    
    def test_get_nested_key(self, config_file):
        """Test getting nested key with dot notation."""
        config = Config(project_root=config_file)
        
        assert config.get("release.ai_enabled") is True
        assert config.get("release.auto_push") is False
    
    def test_get_missing_key_returns_default(self, config_file):
        """Test getting missing key returns default."""
        config = Config(project_root=config_file)
        
        assert config.get("missing") is None
        assert config.get("missing", "default") == "default"
    
    def test_get_release_config(self, config_file):
        """Test getting release configuration."""
        config = Config(project_root=config_file)
        release_config = config.get_release_config()
        
        assert release_config["ai_enabled"] is True
        assert release_config["changelog_file"] == "CHANGELOG.md"
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading when pyproject.toml doesn't exist."""
        config = Config(project_root=tmp_path)
        data = config.load()
        
        assert data == {}
    
    def test_config_caching(self, config_file):
        """Test configuration is cached."""
        config = Config(project_root=config_file)
        
        data1 = config.load()
        data2 = config.load()
        
        assert data1 is data2  # Same object reference
