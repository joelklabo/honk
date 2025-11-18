"""Git integration for Honk Notes (commit editor mode)."""

import os
from typing import Optional


def detect_git_commit_context() -> Optional[dict]:
    """Detect if being invoked as git commit editor.
    
    Checks environment variables that git sets when opening the commit editor.
    
    Returns:
        Dict with git context info, or None if not git commit mode
    """
    git_editor = os.getenv("GIT_EDITOR")
    git_commit_file = os.getenv("GIT_COMMIT_EDITMSG")
    
    # Check for git commit message file
    # Git typically writes to .git/COMMIT_EDITMSG or similar
    if git_commit_file:
        return {
            "mode": "git_commit",
            "file": git_commit_file,
            "template": _get_commit_template()
        }
    
    # Check if editor command mentions honk notes
    if git_editor and "honk notes" in git_editor.lower():
        # May be configured as git editor but no active commit
        return {
            "mode": "git_editor_configured",
            "file": None,
            "template": None
        }
    
    return None


def _get_commit_template() -> str:
    """Get default git commit message template.
    
    Returns:
        Commit message template string
    """
    return """# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
#
# On branch main
# Changes to be committed:
#
"""


def handle_git_commit_mode(config, git_context: dict) -> Optional[int]:
    """Handle git commit editor mode.
    
    Args:
        config: NotesConfig instance
        git_context: Git context dict from detect_git_commit_context()
    
    Returns:
        Exit code if handled (0), None to continue normal flow
    """
    # Only handle if we have a commit file
    if not git_context.get("file"):
        return None
    
    # In non-interactive mode, write template and exit
    # This prevents agents from getting stuck waiting for commit message
    if config.non_interactive or os.getenv("HONK_NOTES_NON_INTERACTIVE") == "1":
        commit_file = git_context['file']
        template = git_context['template']
        
        try:
            with open(commit_file, 'w') as f:
                f.write(template)
            return 0  # Success, git will continue
        except Exception:
            return 1  # Failure
    
    # In interactive mode, let editor open normally
    # User will edit commit message in TUI
    return None


def configure_git_editor(mode: str = "interactive") -> str:
    """Get git editor configuration command.
    
    Args:
        mode: "interactive" or "non-interactive"
    
    Returns:
        Shell command to configure git editor
    """
    if mode == "interactive":
        return 'git config --global core.editor "honk notes edit"'
    else:
        return 'git config --global core.editor "honk notes edit --non-interactive"'
