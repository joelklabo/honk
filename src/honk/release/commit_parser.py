"""Conventional commit message parser."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CommitType(Enum):
    """Standard conventional commit types."""
    
    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    BUILD = "build"
    CI = "ci"
    CHORE = "chore"
    REVERT = "revert"
    
    @classmethod
    def from_string(cls, value: str) -> Optional["CommitType"]:
        """Convert string to CommitType enum."""
        try:
            return cls(value.lower())
        except ValueError:
            return None


@dataclass
class ParsedCommit:
    """Parsed conventional commit information."""
    
    type: Optional[CommitType]
    scope: Optional[str]
    description: str
    body: str
    breaking: bool
    raw_message: str
    
    @property
    def is_feature(self) -> bool:
        """Check if this is a feature commit."""
        return self.type == CommitType.FEAT
    
    @property
    def is_fix(self) -> bool:
        """Check if this is a fix commit."""
        return self.type == CommitType.FIX
    
    @property
    def affects_changelog(self) -> bool:
        """Check if this commit should appear in changelog."""
        # Features, fixes, and breaking changes appear in changelog
        return self.is_feature or self.is_fix or self.breaking


class ConventionalCommitParser:
    """Parser for conventional commit messages."""
    
    @staticmethod
    def parse(message: str) -> ParsedCommit:
        """Parse a conventional commit message.
        
        Format: type(scope): description
        
        With optional:
        - ! for breaking change: type!: or type(scope)!:
        - Body with BREAKING CHANGE: footer
        
        Args:
            message: Full commit message (subject + body)
            
        Returns:
            ParsedCommit with extracted information
        """
        lines = message.split('\n', 1)
        subject = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        
        # Parse subject line
        commit_type = None
        scope = None
        description = subject
        breaking = False
        
        if ':' in subject:
            prefix, desc = subject.split(':', 1)
            description = desc.strip()
            prefix = prefix.strip()
            
            # Check for breaking change indicator (!)
            if '!' in prefix:
                breaking = True
                prefix = prefix.replace('!', '')
            
            # Extract scope if present: type(scope)
            if '(' in prefix and ')' in prefix:
                type_part, scope_part = prefix.split('(', 1)
                scope = scope_part.rstrip(')')
                commit_type = CommitType.from_string(type_part)
            else:
                commit_type = CommitType.from_string(prefix)
        
        # Check for BREAKING CHANGE in body
        if body:
            body_upper = body.upper()
            if 'BREAKING CHANGE:' in body_upper or 'BREAKING-CHANGE:' in body_upper:
                breaking = True
        
        return ParsedCommit(
            type=commit_type,
            scope=scope,
            description=description,
            body=body,
            breaking=breaking,
            raw_message=message
        )
    
    @staticmethod
    def is_conventional(message: str) -> bool:
        """Check if message follows conventional commit format.
        
        Args:
            message: Commit message to check
            
        Returns:
            True if message is conventional commit format
        """
        parsed = ConventionalCommitParser.parse(message)
        return parsed.type is not None


def parse_commit(message: str) -> ParsedCommit:
    """Convenience function to parse a commit message."""
    return ConventionalCommitParser.parse(message)
