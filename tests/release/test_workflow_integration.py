"""Integration tests for release workflow."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from honk.release.workflow import ReleaseWorkflow
from honk.release.analyzer import ReleaseType


class TestReleaseWorkflowIntegration:
    """Integration tests for complete release workflow."""
    
    @pytest.fixture
    def workflow(self, tmp_path):
        """Create workflow with temp directory."""
        return ReleaseWorkflow(project_root=tmp_path)
    
    def test_execute_with_clean_repo(self, workflow):
        """Test workflow execution with clean repo."""
        with patch.object(workflow.git, 'is_working_tree_clean', return_value=True), \
             patch.object(workflow.git, 'get_commits_since_last_tag', return_value=[]), \
             patch.object(workflow.git, 'commit_files'), \
             patch.object(workflow.git, 'create_tag'):
            
            result = workflow.execute(dry_run=True)
            
            assert not result.success
            assert "No commits" in result.error
    
    def test_execute_dry_run_does_not_commit(self, workflow):
        """Test dry run doesn't make changes."""
        mock_commits = [
            MagicMock(message="feat: new feature", sha="abc123")
        ]
        
        with patch.object(workflow.git, 'is_working_tree_clean', return_value=True), \
             patch.object(workflow.git, 'get_commits_since_last_tag', return_value=mock_commits), \
             patch.object(workflow.bumper, 'bump_version', return_value=("0.1.0", "0.2.0")), \
             patch.object(workflow.git, 'commit_files') as mock_commit, \
             patch.object(workflow.git, 'create_tag') as mock_tag:
            
            result = workflow.execute(dry_run=True)
            
            assert result.success
            assert result.new_version == "0.2.0"
            assert mock_commit.call_count == 0
            assert mock_tag.call_count == 0
    
    def test_execute_creates_commit_and_tag(self, workflow):
        """Test workflow creates commit and tag."""
        mock_commits = [
            MagicMock(message="feat: new feature", sha="abc123")
        ]
        
        with patch.object(workflow.git, 'is_working_tree_clean', return_value=True), \
             patch.object(workflow.git, 'get_commits_since_last_tag', return_value=mock_commits), \
             patch.object(workflow.bumper, 'bump_version', return_value=("0.1.0", "0.2.0")), \
             patch.object(workflow.bumper, 'get_version_files', return_value=[Path("pyproject.toml")]), \
             patch.object(workflow.git, 'commit_files', return_value="def456") as mock_commit, \
             patch.object(workflow.git, 'create_tag') as mock_tag:
            
            result = workflow.execute(dry_run=False)
            
            assert result.success
            assert result.new_version == "0.2.0"
            assert result.commit_sha == "def456"
            assert result.tag_name == "v0.2.0"
            assert mock_commit.call_count == 1
            assert mock_tag.call_count == 1
    
    def test_execute_with_explicit_release_type(self, workflow):
        """Test workflow with explicit release type."""
        mock_commits = [
            MagicMock(message="fix: bug fix", sha="abc123")
        ]
        
        with patch.object(workflow.git, 'is_working_tree_clean', return_value=True), \
             patch.object(workflow.git, 'get_commits_since_last_tag', return_value=mock_commits), \
             patch.object(workflow.bumper, 'bump_version', return_value=("0.1.0", "1.0.0")), \
             patch.object(workflow.bumper, 'get_version_files', return_value=[]), \
             patch.object(workflow.git, 'commit_files', return_value="def456"), \
             patch.object(workflow.git, 'create_tag'):
            
            result = workflow.execute(release_type=ReleaseType.MAJOR, dry_run=False)
            
            assert result.success
            assert result.release_type == ReleaseType.MAJOR
            assert result.new_version == "1.0.0"
