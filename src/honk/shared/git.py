"""Shared Git operations for Honk tools."""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class Commit:
    """Represents a Git commit."""
    
    sha: str
    short_sha: str
    author: str
    email: str
    date: datetime
    message: str
    body: str
    
    @property
    def subject(self) -> str:
        """First line of commit message."""
        return self.message.split('\n')[0]
    
    @property
    def type(self) -> Optional[str]:
        """Conventional commit type (feat, fix, etc.)."""
        subject = self.subject
        if ':' in subject:
            prefix = subject.split(':')[0].strip()
            # Handle scope: feat(scope): message
            if '(' in prefix:
                prefix = prefix.split('(')[0]
            return prefix.lower()
        return None
    
    @property
    def scope(self) -> Optional[str]:
        """Conventional commit scope."""
        subject = self.subject
        if '(' in subject and ')' in subject:
            start = subject.index('(') + 1
            end = subject.index(')')
            return subject[start:end]
        return None
    
    @property
    def description(self) -> str:
        """Commit description (after type and scope)."""
        subject = self.subject
        if ':' in subject:
            return subject.split(':', 1)[1].strip()
        return subject
    
    def is_breaking(self) -> bool:
        """Check if this is a breaking change."""
        # Check for ! in type: feat!: or fix!:
        if '!' in self.subject and ':' in self.subject:
            prefix = self.subject.split(':')[0]
            if '!' in prefix:
                return True
        
        # Check for BREAKING CHANGE in body
        body_upper = self.body.upper()
        return 'BREAKING CHANGE' in body_upper or 'BREAKING-CHANGE' in body_upper


class GitOperations:
    """Git operations for release automation."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize Git operations.
        
        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self.repo_path = repo_path or Path.cwd()
    
    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command.
        
        Args:
            *args: Git command arguments
            check: Raise exception on non-zero exit code
            
        Returns:
            CompletedProcess result
        """
        return subprocess.run(
            ['git', '-C', str(self.repo_path), *args],
            capture_output=True,
            text=True,
            check=check
        )
    
    def get_current_version(self) -> Optional[str]:
        """Get current version from latest tag.
        
        Returns:
            Version string (e.g., "0.1.0") or None if no tags
        """
        result = self._run_git('describe', '--tags', '--abbrev=0', check=False)
        if result.returncode != 0:
            return None
        
        tag = result.stdout.strip()
        # Remove 'v' prefix if present
        if tag.startswith('v'):
            tag = tag[1:]
        return tag
    
    def get_commits_since_last_tag(self) -> List[Commit]:
        """Get all commits since the last tag.
        
        Returns:
            List of Commit objects
        """
        # Get last tag
        last_tag_result = self._run_git('describe', '--tags', '--abbrev=0', check=False)
        
        if last_tag_result.returncode == 0:
            last_tag = last_tag_result.stdout.strip()
            rev_range = f"{last_tag}..HEAD"
        else:
            # No tags yet, get all commits
            rev_range = "HEAD"
        
        # Get commit list
        result = self._run_git(
            'log',
            rev_range,
            '--format=%H%x00%h%x00%an%x00%ae%x00%aI%x00%s%x00%b%x00',
            '--no-merges'
        )
        
        commits = []
        for line in result.stdout.split('\x00\x00'):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\x00')
            if len(parts) < 7:
                continue
            
            sha, short_sha, author, email, date_str, subject, body = parts[:7]
            
            # Parse date
            try:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                date = datetime.now()
            
            commits.append(Commit(
                sha=sha,
                short_sha=short_sha,
                author=author,
                email=email,
                date=date,
                message=subject,
                body=body
            ))
        
        return commits
    
    def is_working_tree_clean(self) -> bool:
        """Check if working tree is clean (no uncommitted changes).
        
        Returns:
            True if clean, False if there are uncommitted changes
        """
        result = self._run_git('status', '--porcelain')
        return len(result.stdout.strip()) == 0
    
    def get_current_branch(self) -> str:
        """Get current branch name.
        
        Returns:
            Branch name
        """
        result = self._run_git('rev-parse', '--abbrev-ref', 'HEAD')
        return result.stdout.strip()
    
    def create_tag(self, version: str, message: str) -> None:
        """Create an annotated tag.
        
        Args:
            version: Version string (e.g., "1.0.0")
            message: Tag message
        """
        tag_name = f"v{version}"
        self._run_git('tag', '-a', tag_name, '-m', message)
    
    def push_tag(self, version: str) -> None:
        """Push a tag to remote.
        
        Args:
            version: Version string (e.g., "1.0.0")
        """
        tag_name = f"v{version}"
        self._run_git('push', 'origin', tag_name)
    
    def commit_files(self, files: List[str], message: str) -> str:
        """Stage and commit files.
        
        Args:
            files: List of file paths to commit
            message: Commit message
            
        Returns:
            Commit SHA
        """
        # Stage files
        self._run_git('add', *files)
        
        # Commit
        self._run_git('commit', '-m', message)
        
        # Get commit SHA
        result = self._run_git('rev-parse', 'HEAD')
        return result.stdout.strip()
    
    def push_commits(self, branch: Optional[str] = None) -> None:
        """Push commits to remote.
        
        Args:
            branch: Branch to push (defaults to current branch)
        """
        if branch is None:
            branch = self.get_current_branch()
        self._run_git('push', 'origin', branch)
    
    def has_remote(self, remote: str = 'origin') -> bool:
        """Check if remote exists.
        
        Args:
            remote: Remote name
            
        Returns:
            True if remote exists
        """
        result = self._run_git('remote', 'get-url', remote, check=False)
        return result.returncode == 0
