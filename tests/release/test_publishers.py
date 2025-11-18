"""Unit tests for release publishers."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import os

from honk.release.publishers.pypi import PyPIPublisher
from honk.release.publishers.github import GitHubPublisher


class TestPyPIPublisher:
    """Tests for PyPI publisher."""
    
    @pytest.fixture
    def publisher(self, tmp_path):
        """Create publisher with temp directory."""
        return PyPIPublisher(project_root=tmp_path)
    
    def test_publish_dry_run(self, publisher, tmp_path, capsys):
        """Test dry run doesn't publish."""
        artifacts = [tmp_path / "test.tar.gz"]
        
        publisher.publish(artifacts=artifacts, dry_run=True)
        
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "test.tar.gz" in captured.out
    
    def test_publish_no_token_fails(self, publisher, tmp_path):
        """Test publish without token fails."""
        artifacts = [tmp_path / "test.tar.gz"]
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="PYPI_TOKEN not set"):
                publisher.publish(artifacts=artifacts, dry_run=False)
    
    def test_publish_success(self, publisher, tmp_path):
        """Test successful publish."""
        artifacts = [tmp_path / "test.tar.gz"]
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result), \
             patch.dict(os.environ, {'PYPI_TOKEN': 'test-token'}):
            
            publisher.publish(artifacts=artifacts, dry_run=False)
    
    def test_publish_failure(self, publisher, tmp_path):
        """Test publish failure."""
        artifacts = [tmp_path / "test.tar.gz"]
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Publish failed"
        
        with patch('subprocess.run', return_value=mock_result), \
             patch.dict(os.environ, {'PYPI_TOKEN': 'test-token'}):
            
            with pytest.raises(RuntimeError, match="Publish failed"):
                publisher.publish(artifacts=artifacts, dry_run=False)


class TestGitHubPublisher:
    """Tests for GitHub publisher."""
    
    @pytest.fixture
    def publisher(self, tmp_path):
        """Create publisher with temp directory."""
        return GitHubPublisher(project_root=tmp_path)
    
    def test_create_release_dry_run(self, publisher, capsys):
        """Test dry run doesn't create release."""
        publisher.create_release(
            version="1.0.0",
            changelog="Test release",
            dry_run=True
        )
        
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "v1.0.0" in captured.out
    
    def test_create_release_success(self, publisher):
        """Test successful release creation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            publisher.create_release(
                version="1.0.0",
                changelog="Test release",
                draft=True,
                dry_run=False
            )
            
            # Verify gh CLI was called correctly
            call_args = mock_run.call_args[0][0]
            assert "gh" in call_args
            assert "release" in call_args
            assert "create" in call_args
            assert "v1.0.0" in call_args
            assert "--draft" in call_args
    
    def test_create_release_with_artifacts(self, publisher, tmp_path):
        """Test release with artifacts."""
        artifacts = [tmp_path / "test.tar.gz"]
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            publisher.create_release(
                version="1.0.0",
                changelog="Test release",
                artifacts=artifacts,
                dry_run=False
            )
            
            call_args = mock_run.call_args[0][0]
            assert str(artifacts[0]) in call_args
    
    def test_create_release_failure(self, publisher):
        """Test release creation failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Release failed"
        
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(RuntimeError, match="GitHub release failed"):
                publisher.create_release(
                    version="1.0.0",
                    changelog="Test release",
                    dry_run=False
                )
