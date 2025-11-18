"""Commit analyzer for release type recommendation."""

from dataclasses import dataclass
from enum import Enum
from typing import List

from honk.shared.git import Commit
from honk.release.commit_parser import ConventionalCommitParser, CommitType


class ReleaseType(Enum):
    """Semantic version release types."""
    
    MAJOR = "major"  # Breaking changes: x.0.0
    MINOR = "minor"  # New features: 0.x.0
    PATCH = "patch"  # Bug fixes: 0.0.x
    
    def __str__(self) -> str:
        return self.value


@dataclass
class CommitAnalysis:
    """Analysis results from commits."""
    
    breaking_changes: List[Commit]
    features: List[Commit]
    fixes: List[Commit]
    other: List[Commit]
    recommended_type: ReleaseType
    reasons: List[str]
    
    @property
    def total_commits(self) -> int:
        """Total number of commits analyzed."""
        return (
            len(self.breaking_changes) +
            len(self.features) +
            len(self.fixes) +
            len(self.other)
        )
    
    @property
    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes."""
        return len(self.breaking_changes) > 0
    
    @property
    def has_features(self) -> bool:
        """Check if there are any new features."""
        return len(self.features) > 0
    
    @property
    def has_fixes(self) -> bool:
        """Check if there are any bug fixes."""
        return len(self.fixes) > 0


class CommitAnalyzer:
    """Analyzes commits to recommend release type."""
    
    def __init__(self):
        """Initialize commit analyzer."""
        self.parser = ConventionalCommitParser()
    
    def analyze(self, commits: List[Commit]) -> CommitAnalysis:
        """Analyze commits and recommend release type.
        
        Rules:
        - If any breaking changes → MAJOR
        - If any features (no breaking) → MINOR
        - If only fixes → PATCH
        - If no conventional commits → PATCH (default)
        
        Args:
            commits: List of commits to analyze
            
        Returns:
            CommitAnalysis with categorized commits and recommendation
        """
        breaking_changes = []
        features = []
        fixes = []
        other = []
        
        for commit in commits:
            parsed = self.parser.parse(commit.message)
            
            if parsed.breaking:
                breaking_changes.append(commit)
            elif parsed.type == CommitType.FEAT:
                features.append(commit)
            elif parsed.type == CommitType.FIX:
                fixes.append(commit)
            else:
                other.append(commit)
        
        # Determine release type based on semantic versioning rules
        if breaking_changes:
            recommended = ReleaseType.MAJOR
            reasons = [
                f"Found {len(breaking_changes)} breaking change(s)",
                f"Commits: {', '.join(c.short_sha for c in breaking_changes[:3])}"
            ]
            if len(breaking_changes) > 3:
                reasons[-1] += f" and {len(breaking_changes) - 3} more"
        
        elif features:
            recommended = ReleaseType.MINOR
            reasons = [
                f"Found {len(features)} new feature(s)",
                f"Commits: {', '.join(c.short_sha for c in features[:3])}"
            ]
            if len(features) > 3:
                reasons[-1] += f" and {len(features) - 3} more"
        
        elif fixes:
            recommended = ReleaseType.PATCH
            reasons = [
                f"Found {len(fixes)} bug fix(es)",
                f"Commits: {', '.join(c.short_sha for c in fixes[:3])}"
            ]
            if len(fixes) > 3:
                reasons[-1] += f" and {len(fixes) - 3} more"
        
        else:
            # No conventional commits, default to PATCH
            recommended = ReleaseType.PATCH
            reasons = [
                "No conventional commits found",
                "Defaulting to PATCH release"
            ]
        
        return CommitAnalysis(
            breaking_changes=breaking_changes,
            features=features,
            fixes=fixes,
            other=other,
            recommended_type=recommended,
            reasons=reasons
        )
    
    def get_summary(self, analysis: CommitAnalysis) -> str:
        """Get human-readable summary of analysis.
        
        Args:
            analysis: CommitAnalysis to summarize
            
        Returns:
            Formatted summary string
        """
        lines = [
            f"Analyzed {analysis.total_commits} commit(s):",
            f"  • Breaking changes: {len(analysis.breaking_changes)}",
            f"  • Features: {len(analysis.features)}",
            f"  • Fixes: {len(analysis.fixes)}",
            f"  • Other: {len(analysis.other)}",
            "",
            f"Recommended release type: {analysis.recommended_type.value.upper()}",
            "",
            "Reasoning:"
        ]
        
        for reason in analysis.reasons:
            lines.append(f"  • {reason}")
        
        return "\n".join(lines)
