"""Programmatic API for Honk Notes (agent-friendly buffer access)."""

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .app import StreamingNotesApp


@dataclass
class BufferState:
    """Represents current state of the editor buffer."""
    content: str
    line_count: int
    char_count: int
    dirty: bool
    file_path: Optional[Path]
    cursor_line: int
    cursor_column: int


@dataclass
class EditorState:
    """Represents overall editor state."""
    open: bool
    organizing: bool
    auto_save_enabled: bool
    idle_seconds: int
    last_save: Optional[float]


class NotesAPI:
    """Programmatic API for Honk Notes.
    
    Provides agent-friendly access to buffer and editor state.
    Designed for use by AI agents and automation tools.
    """
    
    def __init__(self, app: "StreamingNotesApp"):
        """Initialize API with app instance.
        
        Args:
            app: The StreamingNotesApp instance to control
        """
        self.app = app
    
    def get_buffer_state(self) -> BufferState:
        """Get current buffer state with metadata.
        
        Returns:
            BufferState with content, cursor position, dirty flag, etc.
        """
        try:
            editor = self.app.query_one("#editor")
            return BufferState(
                content=editor.text,
                line_count=len(editor.text.splitlines()),
                char_count=len(editor.text),
                dirty=getattr(self.app, 'is_dirty', False),
                file_path=self.app.config.file_path,
                cursor_line=getattr(editor, 'cursor_line', 0),
                cursor_column=getattr(editor, 'cursor_column', 0)
            )
        except Exception:
            # Fallback if editor not available
            return BufferState(
                content="",
                line_count=0,
                char_count=0,
                dirty=False,
                file_path=self.app.config.file_path,
                cursor_line=0,
                cursor_column=0
            )
    
    def get_editor_state(self) -> EditorState:
        """Get current editor operational state.
        
        Returns:
            EditorState with status flags and timing info
        """
        try:
            editor = self.app.query_one("#editor")
            return EditorState(
                open=True,
                organizing=getattr(self.app, 'organizing', False),
                auto_save_enabled=self.app.config.auto_save,
                idle_seconds=getattr(editor, 'idle_seconds', 0),
                last_save=getattr(self.app, '_last_save_time', None)
            )
        except Exception:
            return EditorState(
                open=False,
                organizing=False,
                auto_save_enabled=False,
                idle_seconds=0,
                last_save=None
            )
    
    def read_buffer(self) -> str:
        """Read entire buffer content.
        
        Returns:
            Buffer content as string
        """
        try:
            return self.app.query_one("#editor").text
        except Exception:
            return ""
    
    def write_buffer(self, content: str) -> None:
        """Replace entire buffer content.
        
        Args:
            content: New buffer content
        """
        try:
            self.app.query_one("#editor").text = content
        except Exception:
            pass
    
    def append_to_buffer(self, text: str) -> None:
        """Append text to end of buffer.
        
        Args:
            text: Text to append
        """
        try:
            editor = self.app.query_one("#editor")
            editor.text += text
        except Exception:
            pass
    
    def get_line(self, line_number: int) -> str:
        """Get specific line from buffer (0-indexed).
        
        Args:
            line_number: Line index (0-based)
        
        Returns:
            Line content or empty string if out of range
        """
        try:
            lines = self.app.query_one("#editor").text.splitlines()
            return lines[line_number] if 0 <= line_number < len(lines) else ""
        except Exception:
            return ""
    
    def set_line(self, line_number: int, content: str) -> None:
        """Replace specific line in buffer (0-indexed).
        
        Args:
            line_number: Line index (0-based)
            content: New line content
        """
        try:
            lines = self.app.query_one("#editor").text.splitlines()
            if 0 <= line_number < len(lines):
                lines[line_number] = content
                self.app.query_one("#editor").text = "\n".join(lines)
        except Exception:
            pass
    
    async def wait_for_idle(self, timeout: float = 60.0) -> bool:
        """Wait until editor is idle (not organizing).
        
        Args:
            timeout: Maximum seconds to wait
        
        Returns:
            True if became idle, False if timed out
        """
        import asyncio
        start = asyncio.get_event_loop().time()
        
        while getattr(self.app, 'organizing', False):
            if asyncio.get_event_loop().time() - start > timeout:
                return False
            await asyncio.sleep(0.1)
        
        return True
    
    def is_blocking(self) -> bool:
        """Check if editor is in a blocking state.
        
        Returns:
            True if organizing or showing blocking overlay
        """
        if getattr(self.app, 'organizing', False):
            return True
        
        try:
            processing_overlay = self.app.query_one("#processing")
            return processing_overlay.has_class("visible")
        except Exception:
            return False
