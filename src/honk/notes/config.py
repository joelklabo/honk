"""Configuration for Honk Notes application."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class NotesConfig:
    """Configuration for notes application."""

    # File management
    file_path: Optional[Path] = None
    auto_save: bool = True
    auto_save_interval: float = 2.0  # seconds

    # AI organization
    idle_timeout: int = 30  # seconds
    prompt_template: Optional[str] = None
    enable_streaming: bool = True

    # UI settings
    show_line_numbers: bool = False
    theme: str = "monokai"
    language: str = "markdown"

    # Advanced
    max_undo_history: int = 100
    enable_file_drop: bool = True
    
    # Agent-friendly options
    non_interactive: bool = False
    headless: bool = False
    no_prompt: bool = False
    api_port: int = 12345
    no_color: bool = False

    @classmethod
    def load(cls, file_path: Optional[Path] = None) -> "NotesConfig":
        """Load config from file or defaults with environment variable overrides.
        
        Respects environment variables for agent-friendly configuration:
        - HONK_NOTES_NON_INTERACTIVE: Disable TUI
        - HONK_NOTES_NO_PROMPT: Never prompt for input
        - HONK_NOTES_API_PORT: IPC server port
        - HONK_NOTES_HEADLESS: Run in headless mode
        - NO_COLOR: Disable colors (standard)
        """
        # TODO: Load from ~/.config/honk/notes.toml if exists
        config = cls(file_path=file_path)
        
        # Agent-friendly overrides from environment
        if os.getenv("HONK_NOTES_NON_INTERACTIVE") == "1":
            config.non_interactive = True
        
        if os.getenv("HONK_NOTES_NO_PROMPT") == "1":
            config.no_prompt = True
        
        if os.getenv("HONK_NOTES_API_PORT"):
            try:
                config.api_port = int(os.getenv("HONK_NOTES_API_PORT"))
            except ValueError:
                pass
        
        if os.getenv("HONK_NOTES_HEADLESS") == "1":
            config.headless = True
        
        if os.getenv("NO_COLOR"):
            config.no_color = True
        
        return config

    def save(self, path: Optional[Path] = None) -> None:
        """Save config to file."""
        # TODO: Save to ~/.config/honk/notes.toml
        pass
