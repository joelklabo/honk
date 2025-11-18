"""State detection for Honk Notes (LSP-style status and capabilities)."""

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import StreamingNotesApp


class EditorStatus(Enum):
    """Editor operational status (state machine)."""
    IDLE = "idle"                   # Ready for input
    EDITING = "editing"             # User actively typing
    ORGANIZING = "organizing"       # AI processing content
    SAVING = "saving"               # Saving to disk
    LOADING = "loading"             # Loading file
    ERROR = "error"                 # Error state
    CLOSED = "closed"               # Not running


@dataclass
class EditorCapabilities:
    """Editor capabilities (LSP-style capability negotiation)."""
    supports_organization: bool = True
    supports_auto_save: bool = True
    supports_custom_prompts: bool = True
    supports_streaming: bool = True
    supports_ipc: bool = True
    max_file_size_mb: int = 10


class StateDetector:
    """Detect and report editor state for agents.
    
    Provides LSP-style capability negotiation and state detection
    to help agents understand when editor is ready for commands.
    """
    
    def __init__(self, app: "StreamingNotesApp"):
        """Initialize state detector.
        
        Args:
            app: The StreamingNotesApp instance to monitor
        """
        self.app = app
    
    def get_status(self) -> EditorStatus:
        """Get current operational status.
        
        Returns:
            Current EditorStatus enum value
        """
        # Check if app is running
        if not hasattr(self.app, 'is_running') or not self.app.is_running:
            return EditorStatus.CLOSED
        
        # Check for organization in progress
        if getattr(self.app, 'organizing', False):
            return EditorStatus.ORGANIZING
        
        # Check for save operation
        if getattr(self.app, '_saving', False):
            return EditorStatus.SAVING
        
        # Check for load operation
        if getattr(self.app, '_loading', False):
            return EditorStatus.LOADING
        
        # Check for error state
        if getattr(self.app, '_error', False):
            return EditorStatus.ERROR
        
        # Check if actively editing (recent input)
        try:
            editor = self.app.query_one("#editor")
            idle_seconds = getattr(editor, 'idle_seconds', 999)
            if idle_seconds < 2:
                return EditorStatus.EDITING
        except Exception:
            pass
        
        # Default to idle
        return EditorStatus.IDLE
    
    def is_ready(self) -> bool:
        """Check if editor is ready for agent commands.
        
        Returns:
            True if can accept commands now
        """
        status = self.get_status()
        return status in [EditorStatus.IDLE, EditorStatus.EDITING]
    
    def is_blocking(self) -> bool:
        """Check if editor is in a blocking state.
        
        Returns:
            True if agent should wait before sending commands
        """
        status = self.get_status()
        return status in [
            EditorStatus.ORGANIZING,
            EditorStatus.SAVING,
            EditorStatus.LOADING
        ]
    
    def can_accept_input(self) -> bool:
        """Check if editor can accept input right now.
        
        Returns:
            True if safe to send input/commands
        """
        return self.is_ready() and not self.is_blocking()
    
    def get_capabilities(self) -> EditorCapabilities:
        """Get editor capabilities (LSP-style).
        
        Returns:
            EditorCapabilities describing what features are available
        """
        return EditorCapabilities(
            supports_organization=True,
            supports_auto_save=self.app.config.auto_save,
            supports_custom_prompts=self.app.config.prompt_template is not None,
            supports_streaming=getattr(self.app.config, 'enable_streaming', True),
            supports_ipc=hasattr(self.app, 'ipc_server'),
            max_file_size_mb=10
        )
    
    async def wait_until_ready(self, timeout: float = 30.0) -> bool:
        """Block until editor is ready (for agent synchronization).
        
        Args:
            timeout: Maximum seconds to wait
        
        Returns:
            True if became ready, False if timed out
        """
        import asyncio
        start = asyncio.get_event_loop().time()
        
        while not self.is_ready():
            if asyncio.get_event_loop().time() - start > timeout:
                return False
            await asyncio.sleep(0.1)
        
        return True
