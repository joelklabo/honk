"""Tests for commit analyzer."""

from datetime import datetime
from honk.shared.git import Commit
from honk.release.analyzer import CommitAnalyzer, ReleaseType


class TestCommitAnalyzer:
    def test_analyze_breaking_changes(self):
        """Test that breaking changes recommend MAJOR."""
        commits = [
            Commit(
                sha="abc123", short_sha="abc", author="Test",
                email="test@example.com", date=datetime.now(),
                message="feat!: breaking change", body=""
            )
        ]
        
        analyzer = CommitAnalyzer()
        analysis = analyzer.analyze(commits)
        
        assert analysis.recommended_type == ReleaseType.MAJOR
        assert len(analysis.breaking_changes) == 1
    
    def test_analyze_features(self):
        """Test that features recommend MINOR."""
        commits = [
            Commit(
                sha="abc123", short_sha="abc", author="Test",
                email="test@example.com", date=datetime.now(),
                message="feat: new feature", body=""
            )
        ]
        
        analyzer = CommitAnalyzer()
        analysis = analyzer.analyze(commits)
        
        assert analysis.recommended_type == ReleaseType.MINOR
        assert len(analysis.features) == 1
    
    def test_analyze_fixes(self):
        """Test that fixes recommend PATCH."""
        commits = [
            Commit(
                sha="abc123", short_sha="abc", author="Test",
                email="test@example.com", date=datetime.now(),
                message="fix: bug fix", body=""
            )
        ]
        
        analyzer = CommitAnalyzer()
        analysis = analyzer.analyze(commits)
        
        assert analysis.recommended_type == ReleaseType.PATCH
        assert len(analysis.fixes) == 1
