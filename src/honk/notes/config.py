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
    default_notes_dir: Path = Path.home() / ".honk" / "notes" / "scratchpad"

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

    # Retry configuration
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 10.0
    
    # Agent-friendly options
    non_interactive: bool = False
    headless: bool = False
    no_prompt: bool = False
    api_port: int = 12345
    no_color: bool = False

    @classmethod
    def load(
        cls,
        file_path: Optional[Path] = None,
        idle_timeout: Optional[int] = None,
        auto_save: Optional[bool] = None,
        prompt_template: Optional[str] = None,
        default_notes_dir: Optional[Path] = None,
    ) -> "NotesConfig":
        """Load config from file or defaults with environment variable overrides.
        
        Respects environment variables for agent-friendly configuration:
        - HONK_NOTES_NON_INTERACTIVE: Disable TUI
        - HONK_NOTES_NO_PROMPT: Never prompt for input
        - HONK_NOTES_API_PORT: IPC server port
        - HONK_NOTES_HEADLESS: Run in headless mode
        - NO_COLOR: Disable colors (standard)
        """
        # TODO: Load from ~/.config/honk/notes.toml if exists
        config = cls(
            file_path=file_path,
            idle_timeout=idle_timeout if idle_timeout is not None else cls.idle_timeout,
            auto_save=auto_save if auto_save is not None else cls.auto_save,
            prompt_template=prompt_template if prompt_template is not None else cls.prompt_template,
            default_notes_dir=default_notes_dir if default_notes_dir is not None else cls.default_notes_dir,
        )

        # If no file_path is provided, use a default in the punk_managers directory
        if config.file_path is None:
            config.default_notes_dir.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config.file_path = config.default_notes_dir / f"untitled_{timestamp}.md"
        
        # Agent-friendly overrides from environment
        if os.getenv("HONK_NOTES_NON_INTERACTIVE") == "1":
            config.non_interactive = True
        
        if os.getenv("HONK_NOTES_NO_PROMPT") == "1":
            config.no_prompt = True
        
        if os.getenv("HONK_NOTES_API_PORT"):
            try:
                port_str = os.getenv("HONK_NOTES_API_PORT")
                if port_str:
                    config.api_port = int(port_str)
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
