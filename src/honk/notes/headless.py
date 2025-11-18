"""Headless mode for Honk Notes (non-interactive, API-only)."""

from .config import NotesConfig


def run_headless_mode(config: NotesConfig) -> int:
    """Run in headless mode (no TUI).
    
    Args:
        config: Configuration with headless/non_interactive flags set
    
    Returns:
        Exit code (0 for success)
    """
    # Read file if it exists
    if config.file_path and config.file_path.exists():
        content = config.file_path.read_text()
    else:
        content = ""
    
    # If API mode requested, start IPC server
    if config.api_port and config.headless:
        # IPC server will be implemented in Phase 3
        # For now, just return success
        pass
    
    # In non-interactive mode, just exit cleanly
    # Agents will use agent-* commands for operations
    return 0
