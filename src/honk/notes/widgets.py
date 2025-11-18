"""Custom widgets for Honk Notes application."""

import asyncio
import time
from textual.widgets import TextArea, Static
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text


class IdleReached(Message):
    """Emitted when editor has been idle for threshold time."""

    def __init__(self, content: str) -> None:
        self.content = content
        super().__init__()


class StreamingTextArea(TextArea):
    """TextArea with idle detection and streaming updates.
    
    Uses Honk's design system for consistent styling.
    """

    # Reactive properties
    last_change = reactive(0.0)
    idle_seconds = reactive(0)
    is_updating = reactive(False)

    def __init__(
        self,
        idle_timeout: int = 30,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.idle_timeout = idle_timeout
        self._idle_watcher = None
        self._update_lock = asyncio.Lock()

    def on_mount(self) -> None:
        """Start idle detection on mount."""
        self._idle_watcher = asyncio.create_task(self._watch_idle())

    def on_unmount(self) -> None:
        """Clean up on unmount."""
        if self._idle_watcher:
            self._idle_watcher.cancel()

    async def _watch_idle(self) -> None:
        """Monitor idle time without polling."""
        while True:
            await asyncio.sleep(1)
            if self.last_change > 0 and not self.is_updating:
                elapsed = time.time() - self.last_change
                self.idle_seconds = int(elapsed)

                if elapsed >= self.idle_timeout:
                    # Emit idle event
                    self.post_message(IdleReached(self.text))
                    self.last_change = 0  # Reset

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Track text changes."""
        if not self.is_updating:
            self.last_change = time.time()
            self.idle_seconds = 0

    async def apply_incremental_update(self, new_content: str) -> None:
        """Apply new content with smooth incremental updates."""
        async with self._update_lock:
            self.is_updating = True
            try:
                await self._apply_diff(self.text, new_content)
            finally:
                self.is_updating = False
                self.last_change = time.time()

    async def _apply_diff(self, old: str, new: str) -> None:
        """Apply diff incrementally for smooth visual update."""
        # For MVP, just replace all content
        # TODO: Implement line-by-line diff animation
        self.text = new
        await asyncio.sleep(0.1)  # Brief pause for visual feedback


class ProcessingOverlay(Container):
    """Floating progress indicator overlay using Honk's design system."""

    DEFAULT_CSS = """
    ProcessingOverlay {
        layer: overlay;
        align: center middle;
        width: 70;
        height: 9;
        background: $surface;
        border: heavy $primary;
        display: none;
        padding: 1 2;
    }

    ProcessingOverlay.visible {
        display: block;
    }

    ProcessingOverlay > Vertical {
        height: auto;
        align: center middle;
    }

    #progress-icon {
        text-align: center;
        color: $accent;
        margin-bottom: 1;
    }

    #progress-message {
        text-align: center;
        color: $text;
        margin-bottom: 1;
    }

    #progress-bar {
        text-align: center;
        color: $primary;
    }

    #progress-percent {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self):
        with Vertical():
            yield Static("🤖", id="progress-icon", classes="brand")
            yield Static("", id="progress-message")
            yield Static("", id="progress-bar")
            yield Static("", id="progress-percent")

    def show(self, message: str = "Processing...") -> None:
        """Show overlay with initial message."""
        self.add_class("visible")
        msg_widget = self.query_one("#progress-message", Static)
        msg_widget.update(Text(message, style="bold"))

    def update_progress(self, percent: float, message: str = None) -> None:
        """Update progress bar with Honk's design aesthetic."""
        bar_length = 40
        filled = int(bar_length * percent)
        
        # Use Honk's brand color for filled portion
        filled_bar = "━" * filled
        empty_bar = "╌" * (bar_length - filled)
        
        bar_widget = self.query_one("#progress-bar", Static)
        bar_widget.update(Text(f"{filled_bar}{empty_bar}", style="cyan"))
        
        percent_widget = self.query_one("#progress-percent", Static)
        percent_widget.update(Text(f"{int(percent * 100)}%", style="dim"))

        if message:
            msg_widget = self.query_one("#progress-message", Static)
            msg_widget.update(Text(message, style="bold"))

    def hide(self) -> None:
        """Hide overlay."""
        self.remove_class("visible")
