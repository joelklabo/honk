"""Tests for conventional commit parser."""

import pytest
from honk.release.commit_parser import (
    ConventionalCommitParser,
    ParsedCommit,
    CommitType,
    parse_commit
)


class TestConventionalCommitParser:
    """Tests for ConventionalCommitParser."""
    
    def test_parse_simple_feature(self):
        """Test parsing simple feature commit."""
        message = "feat: add new feature"
        parsed = ConventionalCommitParser.parse(message)
        
        assert parsed.type == CommitType.FEAT
        assert parsed.scope is None
        assert parsed.description == "add new feature"
        assert parsed.body == ""
        assert parsed.breaking is False
    
    def test_parse_fix_with_scope(self):
        """Test parsing fix commit with scope."""
        message = "fix(api): resolve authentication bug"
        parsed = ConventionalCommitParser.parse(message)
        
        assert parsed.type == CommitType.FIX
        assert parsed.scope == "api"
        assert parsed.description == "resolve authentication bug"
        assert parsed.breaking is False
    
    def test_parse_breaking_with_exclamation(self):
        """Test parsing breaking change with ! indicator."""
        message = "feat!: remove deprecated API"
        parsed = ConventionalCommitParser.parse(message)
        
        assert parsed.type == CommitType.FEAT
        assert parsed.breaking is True
    
    def test_is_conventional(self):
        """Test checking if message is conventional."""
        assert ConventionalCommitParser.is_conventional("feat: add feature") is True
        assert ConventionalCommitParser.is_conventional("Random message") is False
