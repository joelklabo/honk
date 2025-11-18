"""Release workflow orchestration."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from honk.shared.git import GitOperations
from honk.release.analyzer import CommitAnalyzer, ReleaseType
from honk.release.versioning.bumper import VersionBumper
from honk.release.changelog.ai_generator import AIChangelogGenerator


@dataclass
class ReleaseResult:
    """Result of a release operation."""
    
    success: bool
    old_version: str
    new_version: str
    release_type: ReleaseType
    changelog: str
    commit_sha: Optional[str] = None
    tag_name: Optional[str] = None
    error: Optional[str] = None


class ReleaseWorkflow:
    """Orchestrates the release workflow."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize release workflow.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.git = GitOperations(self.project_root)
        self.analyzer = CommitAnalyzer()
        self.bumper = VersionBumper(self.project_root)
        self.changelog_gen = AIChangelogGenerator()
    
    def execute(
        self,
        release_type: Optional[ReleaseType] = None,
        dry_run: bool = False,
        use_ai: bool = True
    ) -> ReleaseResult:
        """Execute complete release workflow.
        
        Args:
            release_type: Explicit release type (or None to auto-detect)
            dry_run: If True, don't make changes
            use_ai: If True, use AI for changelog generation
            
        Returns:
            ReleaseResult with operation details
        """
        try:
            # 1. Pre-flight checks
            if not dry_run and not self.git.is_working_tree_clean():
                return ReleaseResult(
                    success=False,
                    old_version="",
                    new_version="",
                    release_type=ReleaseType.PATCH,
                    changelog="",
                    error="Working tree is not clean"
                )
            
            # 2. Analyze commits
            commits = self.git.get_commits_since_last_tag()
            if not commits:
                return ReleaseResult(
                    success=False,
                    old_version="",
                    new_version="",
                    release_type=ReleaseType.PATCH,
                    changelog="",
                    error="No commits since last release"
                )
            
            analysis = self.analyzer.analyze(commits)
            
            # Use provided release type or recommended one
            final_release_type = release_type or analysis.recommended_type
            
            # 3. Bump version
            old_version, new_version = self.bumper.bump_version(
                final_release_type,
                dry_run=dry_run
            )
            
            # 4. Generate changelog
            changelog = self.changelog_gen.generate(commits, str(new_version))
            
            # 5. Commit and tag (if not dry run)
            commit_sha = None
            tag_name = None
            
            if not dry_run:
                # Commit version changes
                version_files = [
                    str(f.relative_to(self.project_root))
                    for f in self.bumper.get_version_files()
                ]
                commit_msg = f"chore(release): bump version to {new_version}"
                commit_sha = self.git.commit_files(version_files, commit_msg)
                
                # Create tag
                tag_name = f"v{new_version}"
                self.git.create_tag(str(new_version), f"Release {new_version}")
            
            return ReleaseResult(
                success=True,
                old_version=str(old_version),
                new_version=str(new_version),
                release_type=final_release_type,
                changelog=changelog,
                commit_sha=commit_sha,
                tag_name=tag_name
            )
            
        except Exception as e:
            return ReleaseResult(
                success=False,
                old_version="",
                new_version="",
                release_type=ReleaseType.PATCH,
                changelog="",
                error=str(e)
            )
