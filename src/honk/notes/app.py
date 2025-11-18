"""Main Textual application for Honk Notes."""

import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TextArea
from textual.reactive import reactive
from .widgets import StreamingTextArea, ProcessingOverlay, IdleReached
from .organizer import AIOrganizer
from .auto_save import AutoSaver
from .config import NotesConfig


class StreamingNotesApp(App):
    """AI-assisted notes application using Honk's design system."""

    CSS = """
    /* Honk Notes - Design System Integration */
    
    StreamingTextArea {
        height: 100%;
        border: none;
        background: $surface;
    }
    
    Header {
        background: $primary;
        color: $text;
    }
    
    Footer {
        background: $surface;
        color: $text-muted;
    }
    
    .brand {
        color: $accent;
    }
    """

    BINDINGS = [
        ("ctrl+s", "save", "💾 Save"),
        ("ctrl+o", "organize_now", "🤖 Organize"),
        ("ctrl+z", "undo", "↶ Undo"),
        ("ctrl+q", "quit", "Quit"),
    ]

    organizing = reactive(False)

    def __init__(self, config: NotesConfig):
        super().__init__()
        self.config = config
        self.organizer = AIOrganizer(config.prompt_template)
        self.auto_saver = None
        self.is_dirty = False
        
        # Agent-friendly components
        from .api import NotesAPI
        from .state import StateDetector
        self.api = NotesAPI(self)
        self.state_detector = StateDetector(self)
        self.ipc_server = None

        if config.file_path and config.auto_save:
            self.auto_saver = AutoSaver(
                config.file_path,
                config.auto_save_interval
            )

    def compose(self) -> ComposeResult:
        yield Header()

        # Load initial content
        initial_content = ""
        if self.config.file_path and self.config.file_path.exists():
            initial_content = self.config.file_path.read_text()

        yield StreamingTextArea(
            text=initial_content,
            language=self.config.language,
            theme=self.config.theme,
            show_line_numbers=self.config.show_line_numbers,
            idle_timeout=self.config.idle_timeout,
            id="editor"
        )
        yield ProcessingOverlay(id="processing")
        yield Footer()

    async def on_mount(self) -> None:
        """Set up title and start IPC if configured."""
        filename = self.config.file_path.name if self.config.file_path else "Untitled"
        self.title = f"Honk Notes - {filename}"
        self.sub_title = f"Idle: 0s | Ctrl+O: Organize | Ctrl+S: Save"
        
        # Start IPC server if configured
        if self.config.api_port and self.config.headless:
            from .ipc import NotesIPCServer
            self.ipc_server = NotesIPCServer(self, self.config.api_port)
            asyncio.create_task(self.ipc_server.start())

    async def on_streaming_text_area_idle_reached(
        self,
        message: IdleReached
    ) -> None:
        """Handle idle event from editor."""
        if not self.organizing:
            await self._organize_content(message.content)

    async def action_organize_now(self) -> None:
        """Manually trigger organization."""
        if not self.organizing:
            editor = self.query_one("#editor", StreamingTextArea)
            await self._organize_content(editor.text)

    async def _organize_content(self, content: str) -> None:
        """Organize content with AI."""
        if not content.strip():
            return

        self.organizing = True
        editor = self.query_one("#editor", StreamingTextArea)
        overlay = self.query_one("#processing", ProcessingOverlay)

        try:
            overlay.show("🤖 AI is organizing your notes...")

            # Stream organized content
            async for partial, progress in self.organizer.organize_stream(content):
                overlay.update_progress(progress, "Organizing...")

            # Apply final result
            final_organized = partial
            await editor.apply_incremental_update(final_organized)

            overlay.update_progress(1.0, "✓ Done!")
            await asyncio.sleep(0.5)

        except Exception as e:
            self.notify(f"Organization failed: {e}", severity="error")
        finally:
            overlay.hide()
            self.organizing = False

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes for auto-save."""
        self.is_dirty = True
        if self.auto_saver and not self.organizing:
            asyncio.create_task(
                self.auto_saver.schedule_save(event.text_area.text)
            )

    def action_save(self) -> None:
        """Manually save file."""
        if self.config.file_path:
            editor = self.query_one("#editor", StreamingTextArea)
            self.config.file_path.write_text(editor.text)
            self.is_dirty = False
            self.notify("✓ Saved", timeout=2)
        else:
            self.notify("No file specified", severity="warning")
    
    async def action_quit(self) -> None:
        """Quit and cleanup."""
        if self.ipc_server:
            self.ipc_server.stop()
        await super().action_quit()
