"""Tests for shared Git operations."""

import pytest
from datetime import datetime
from honk.shared.git import Commit, GitOperations


class TestCommit:
    """Tests for Commit dataclass."""
    
    def test_subject_extraction(self):
        """Test extracting subject from message."""
        commit = Commit(
            sha="abc123",
            short_sha="abc",
            author="Test",
            email="test@example.com",
            date=datetime.now(),
            message="feat: add new feature\n\nLonger description",
            body="Longer description"
        )
        assert commit.subject == "feat: add new feature"
    
    def test_type_extraction(self):
        """Test conventional commit type extraction."""
        test_cases = [
            ("feat: add feature", "feat"),
            ("fix: bug fix", "fix"),
            ("feat(scope): add feature", "feat"),
            ("chore: update deps", "chore"),
            ("No type message", None),
        ]
        
        for message, expected_type in test_cases:
            commit = Commit(
                sha="abc", short_sha="abc", author="Test",
                email="test@example.com", date=datetime.now(),
                message=message, body=""
            )
            assert commit.type == expected_type
    
    def test_is_breaking_with_exclamation(self):
        """Test breaking change detection with ! syntax."""
        commit = Commit(
            sha="abc", short_sha="abc", author="Test",
            email="test@example.com", date=datetime.now(),
            message="feat!: breaking change", body=""
        )
        assert commit.is_breaking() is True
