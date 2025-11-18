"""Unit tests for release builders."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import subprocess

from honk.release.builders.pypi import PyPIBuilder
from honk.release.builders.homebrew import HomebrewBuilder


class TestPyPIBuilder:
    """Tests for PyPI builder."""
    
    @pytest.fixture
    def builder(self, tmp_path):
        """Create builder with temp directory."""
        return PyPIBuilder(project_root=tmp_path)
    
    def test_build_success(self, builder):
        """Test successful build."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result), \
             patch.object(builder.dist_dir, 'exists', return_value=True), \
             patch.object(builder.dist_dir, 'glob', return_value=[Path("dist/pkg.tar.gz")]):
            
            artifacts = builder.build()
            
            assert len(artifacts) == 1
            assert artifacts[0].name == "pkg.tar.gz"
    
    def test_build_failure(self, builder):
        """Test build failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Build failed"
        
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(RuntimeError, match="Build failed"):
                builder.build()
    
    def test_clean_removes_dist(self, builder, tmp_path):
        """Test clean removes dist directory."""
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        (dist_dir / "test.txt").write_text("test")
        
        builder.clean()
        
        assert not dist_dir.exists()
    
    def test_get_artifacts_empty(self, builder):
        """Test get artifacts when dist doesn't exist."""
        artifacts = builder.get_artifacts()
        
        assert len(artifacts) == 0


class TestHomebrewBuilder:
    """Tests for Homebrew builder."""
    
    @pytest.fixture
    def builder(self, tmp_path):
        """Create builder with temp directory."""
        return HomebrewBuilder(project_root=tmp_path)
    
    def test_generate_formula(self, builder):
        """Test formula generation."""
        formula = builder.generate_formula(
            version="1.0.0",
            description="Test package",
            homepage="https://example.com",
            tarball_url="https://example.com/test.tar.gz",
            sha256="abc123"
        )
        
        assert "class Honk < Formula" in formula
        assert "Test package" in formula
        assert "https://example.com" in formula
        assert "abc123" in formula
        assert "depends_on \"python@3.12\"" in formula
    
    def test_calculate_sha256(self, builder, tmp_path):
        """Test SHA256 calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        sha256 = builder.calculate_sha256(test_file)
        
        assert len(sha256) == 64
        assert sha256.isalnum()
