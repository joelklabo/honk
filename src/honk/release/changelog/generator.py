"""Traditional changelog generator (non-AI fallback)."""

from datetime import datetime
from typing import Dict, List

from honk.shared.git import Commit
from honk.release.commit_parser import ConventionalCommitParser, CommitType


class ChangelogGenerator:
    """Generates changelogs from commits (Keep a Changelog format)."""
    
    def __init__(self):
        """Initialize changelog generator."""
        self.parser = ConventionalCommitParser()
    
    def generate(self, commits: List[Commit], version: str) -> str:
        """Generate changelog entry for commits.
        
        Args:
            commits: List of commits to include
            version: Version number for this release
            
        Returns:
            Formatted changelog text (Keep a Changelog format)
        """
        # Group commits by section
        sections: Dict[str, List[str]] = {
            "Added": [],
            "Changed": [],
            "Deprecated": [],
            "Removed": [],
            "Fixed": [],
            "Security": []
        }
        
        breaking_changes: List[str] = []
        
        for commit in commits:
            parsed = self.parser.parse(commit.message)
            
            # Skip non-conventional commits
            if parsed.type is None:
                continue
            
            entry = f"- {parsed.description}"
            if parsed.scope:
                entry = f"- **{parsed.scope}**: {parsed.description}"
            
            # Categorize by type
            if parsed.breaking:
                breaking_changes.append(entry)
            
            if parsed.type == CommitType.FEAT:
                sections["Added"].append(entry)
            elif parsed.type == CommitType.FIX:
                sections["Fixed"].append(entry)
            elif parsed.type == CommitType.DOCS:
                sections["Changed"].append(entry)
            elif parsed.type == CommitType.PERF:
                sections["Changed"].append(entry)
            elif parsed.type == CommitType.REFACTOR:
                sections["Changed"].append(entry)
            # Security commits go to Security section
            elif parsed.scope == "security" or "security" in parsed.description.lower():
                sections["Security"].append(entry)
        
        # Build changelog entry
        lines = [
            f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}",
            ""
        ]
        
        # Add breaking changes first if any
        if breaking_changes:
            lines.append("### ⚠️ BREAKING CHANGES")
            lines.append("")
            lines.extend(breaking_changes)
            lines.append("")
        
        # Add sections with content
        for section, entries in sections.items():
            if entries:
                lines.append(f"### {section}")
                lines.append("")
                lines.extend(sorted(set(entries)))  # Remove duplicates and sort
                lines.append("")
        
        return "\n".join(lines)
    
    def update_changelog_file(
        self,
        version: str,
        entry: str,
        changelog_path: str = "CHANGELOG.md"
    ) -> None:
        """Update CHANGELOG.md file with new entry.
        
        Args:
            version: Version number
            entry: Changelog entry text
            changelog_path: Path to CHANGELOG.md file
        """
        from pathlib import Path
        
        changelog_file = Path(changelog_path)
        
        if not changelog_file.exists():
            # Create new changelog
            content = [
                "# Changelog",
                "",
                "All notable changes to this project will be documented in this file.",
                "",
                "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
                "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
                "",
                entry
            ]
            changelog_file.write_text("\n".join(content))
        else:
            # Insert new entry after header
            content = changelog_file.read_text()
            lines = content.split("\n")
            
            # Find insertion point (after header and intro)
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## ["):
                    insert_idx = i
                    break
            
            if insert_idx == 0:
                # No previous entries, insert after intro
                for i, line in enumerate(lines):
                    if line.strip() == "" and i > 5:  # After header block
                        insert_idx = i + 1
                        break
            
            # Insert new entry
            entry_lines = entry.split("\n")
            lines[insert_idx:insert_idx] = entry_lines + [""]
            
            changelog_file.write_text("\n".join(lines))
