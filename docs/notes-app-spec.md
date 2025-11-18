# Honk Notes - AI-Assisted Note-Taking Application
## Implementation Specification v1.0

**Date**: 2025-11-18  
**Architecture**: Proposal 2 - Single-Pane Incremental Update  
**Status**: Ready for Implementation

---

## Executive Summary

Honk Notes is a terminal-based note-taking application that automatically organizes notes using GitHub Copilot CLI after 30 seconds of idle time. Built with Textual for flicker-free, event-driven UI, it provides a seamless editing experience with intelligent AI assistance.

**Key Features**:
- Single-pane text editor with markdown support
- Automatic AI organization after idle period
- Manual organization on-demand (Ctrl+O)
- Auto-save with debounce
- Streaming progress indicators
- Event-driven (no polling)
- File drag-and-drop support

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    StreamingNotesApp                     │
│                   (Main Textual App)                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │         StreamingTextArea                       │   │
│  │  - Live editing                                 │   │
│  │  - Idle detection                               │   │
│  │  - Incremental updates                          │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │         ProcessingOverlay (when active)         │   │
│  │  🤖 AI is organizing... ━━━━━━━━ 45%           │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
         │                             │
         ├── AIOrganizer              ├── AutoSaver
         │   (Copilot CLI)            │   (Debounced saves)
         │                            │
         └── IdleDetector              └── FileWatcher
             (30s timeout)                 (Optional)
```

---

## File Structure

```
src/honk/notes/
├── __init__.py              # Package exports
├── cli.py                   # Typer CLI commands
├── app.py                   # StreamingNotesApp (main app)
├── widgets.py               # StreamingTextArea, ProcessingOverlay
├── organizer.py             # AIOrganizer (Copilot integration)
├── config.py                # NotesConfig (configuration)
├── auto_save.py             # AutoSaver (debounced saving)
└── prompts.py               # AI prompt templates

tests/notes/
├── test_app.py              # App integration tests
├── test_organizer.py        # AI organizer tests
├── test_auto_save.py        # Auto-save tests
└── fixtures/                # Test data
    └── sample_notes.md
```

---

## Component Specifications

### 1. NotesConfig (config.py)

**Purpose**: Configuration dataclass for notes app settings

```python
from dataclasses import dataclass, field
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
    
    @classmethod
    def load(cls, file_path: Optional[Path] = None) -> "NotesConfig":
        """Load config from file or defaults."""
        # TODO: Load from ~/.config/honk/notes.toml if exists
        return cls(file_path=file_path)
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save config to file."""
        # TODO: Save to ~/.config/honk/notes.toml
        pass
```

---

### 2. StreamingTextArea (widgets.py)

**Purpose**: Enhanced TextArea with idle detection and incremental updates

**Key Features**:
- Tracks last edit time for idle detection
- Emits custom events when idle threshold reached
- Applies incremental updates smoothly
- Handles text diffs efficiently

```python
from textual.widgets import TextArea
from textual.reactive import reactive
from textual.message import Message
import asyncio
import time
import difflib

class IdleReached(Message):
    """Emitted when editor has been idle for threshold time."""
    
    def __init__(self, content: str) -> None:
        self.content = content
        super().__init__()

class StreamingTextArea(TextArea):
    """TextArea with idle detection and streaming updates."""
    
    # Reactive properties
    last_change = reactive(0.0)
    idle_seconds = reactive(0)
    is_updating = reactive(False)
    
    def __init__(
        self,
        idle_timeout: int = 30,
        **kwargs
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
```

---

### 3. ProcessingOverlay (widgets.py)

**Purpose**: Floating progress indicator during AI processing

```python
from textual.widgets import Static
from textual.containers import Container

class ProcessingOverlay(Container):
    """Floating progress indicator overlay."""
    
    CSS = """
    ProcessingOverlay {
        layer: overlay;
        align: center middle;
        width: 60;
        height: 7;
        background: $panel;
        border: heavy $accent;
        display: none;
    }
    
    ProcessingOverlay.visible {
        display: block;
    }
    
    #progress-message {
        text-align: center;
        padding: 1;
    }
    
    #progress-bar {
        text-align: center;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def compose(self):
        yield Static("", id="progress-message")
        yield Static("", id="progress-bar")
    
    def show(self, message: str = "Processing...") -> None:
        """Show overlay with initial message."""
        self.add_class("visible")
        msg_widget = self.query_one("#progress-message", Static)
        msg_widget.update(f"[bold cyan]{message}[/]")
    
    def update_progress(self, percent: float, message: str = None) -> None:
        """Update progress bar."""
        bar_length = 40
        filled = int(bar_length * percent)
        bar = "━" * filled + "╸" + "─" * (bar_length - filled - 1)
        
        bar_widget = self.query_one("#progress-bar", Static)
        bar_widget.update(f"{bar} {int(percent * 100)}%")
        
        if message:
            msg_widget = self.query_one("#progress-message", Static)
            msg_widget.update(f"[bold cyan]{message}[/]")
    
    def hide(self) -> None:
        """Hide overlay."""
        self.remove_class("visible")
```

---

### 4. AIOrganizer (organizer.py)

**Purpose**: Integration with GitHub Copilot CLI for AI organization

```python
import asyncio
from typing import AsyncIterator, Optional
from pathlib import Path

class AIOrganizer:
    """Manages AI organization via GitHub Copilot CLI."""
    
    DEFAULT_PROMPT = """Organize the following notes into clear, structured sections.

Guidelines:
- Use markdown headers (##) for main sections
- Group related items together logically
- Add checkboxes [ ] for action items
- Add > blockquotes for important notes
- Preserve all original information
- Make it more scannable and organized

Notes to organize:
{content}

Return only the organized markdown, no explanations."""
    
    def __init__(self, prompt_template: Optional[str] = None):
        self.prompt_template = prompt_template or self.DEFAULT_PROMPT
    
    async def organize(self, content: str) -> str:
        """Organize content using GitHub Copilot CLI."""
        prompt = self.prompt_template.format(content=content)
        
        # Call GitHub Copilot CLI
        proc = await asyncio.create_subprocess_exec(
            "gh", "copilot", "suggest",
            "-t", "shell",
            prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Copilot CLI failed: {stderr.decode()}")
        
        return stdout.decode().strip()
    
    async def organize_stream(
        self, 
        content: str
    ) -> AsyncIterator[tuple[str, float]]:
        """
        Stream organized content incrementally.
        Yields (partial_content, progress) tuples.
        """
        # For MVP, we'll simulate streaming by yielding full result
        # TODO: Implement true streaming if Copilot CLI supports it
        result = await self.organize(content)
        
        # Simulate progressive reveal
        lines = result.splitlines()
        accumulated = []
        
        for i, line in enumerate(lines):
            accumulated.append(line)
            progress = (i + 1) / len(lines)
            yield ("\n".join(accumulated), progress)
            await asyncio.sleep(0.05)  # Smooth animation
```

---

### 5. AutoSaver (auto_save.py)

**Purpose**: Debounced auto-save functionality

```python
import asyncio
from pathlib import Path
from typing import Optional

class AutoSaver:
    """Debounced auto-save handler."""
    
    def __init__(
        self,
        file_path: Path,
        debounce_seconds: float = 2.0
    ):
        self.file_path = file_path
        self.debounce_seconds = debounce_seconds
        self._save_task: Optional[asyncio.Task] = None
    
    async def schedule_save(self, content: str) -> None:
        """Schedule a debounced save."""
        if self._save_task:
            self._save_task.cancel()
        
        self._save_task = asyncio.create_task(
            self._debounced_save(content)
        )
    
    async def _debounced_save(self, content: str) -> None:
        """Wait debounce period and save."""
        try:
            await asyncio.sleep(self.debounce_seconds)
            self.file_path.write_text(content)
        except asyncio.CancelledError:
            # New edit came in, this save was cancelled
            pass
    
    def save_now(self, content: str) -> None:
        """Save immediately (synchronous)."""
        self.file_path.write_text(content)
```

---

### 6. StreamingNotesApp (app.py)

**Purpose**: Main Textual application

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.reactive import reactive
from pathlib import Path
from .widgets import StreamingTextArea, ProcessingOverlay, IdleReached
from .organizer import AIOrganizer
from .auto_save import AutoSaver
from .config import NotesConfig

class StreamingNotesApp(App):
    """AI-assisted notes application."""
    
    CSS = """
    StreamingTextArea {
        height: 100%;
    }
    """
    
    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("ctrl+o", "organize_now", "Organize Now"),
        ("ctrl+q", "quit", "Quit"),
    ]
    
    organizing = reactive(False)
    
    def __init__(self, config: NotesConfig):
        super().__init__()
        self.config = config
        self.organizer = AIOrganizer(config.prompt_template)
        self.auto_saver = None
        
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
    
    def on_mount(self) -> None:
        """Set up title."""
        filename = self.config.file_path.name if self.config.file_path else "Untitled"
        self.title = f"Honk Notes - {filename}"
        self.sub_title = f"Idle: 0s | Ctrl+O: Organize | Ctrl+S: Save"
    
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
        if self.auto_saver and not self.organizing:
            asyncio.create_task(
                self.auto_saver.schedule_save(event.text_area.text)
            )
    
    def action_save(self) -> None:
        """Manually save file."""
        if self.config.file_path:
            editor = self.query_one("#editor", StreamingTextArea)
            self.config.file_path.write_text(editor.text)
            self.notify("✓ Saved", timeout=2)
        else:
            self.notify("No file specified", severity="warning")
```

---

### 7. CLI Integration (cli.py)

**Purpose**: Typer CLI commands for Honk Notes

```python
import typer
from pathlib import Path
from typing import Optional
from .app import StreamingNotesApp
from .config import NotesConfig
from honk.ui import print_error, print_success

notes_app = typer.Typer()

@notes_app.command()
def edit(
    file: Optional[Path] = typer.Argument(
        None, 
        help="File to edit (creates if doesn't exist)"
    ),
    idle_timeout: int = typer.Option(
        30,
        "--idle", "-i",
        help="Seconds of idle time before AI organization"
    ),
    no_auto_save: bool = typer.Option(
        False,
        "--no-auto-save",
        help="Disable auto-save"
    ),
    prompt: Optional[Path] = typer.Option(
        None,
        "--prompt", "-p",
        help="Custom AI prompt template file"
    ),
):
    """
    Open AI-assisted notes editor.
    
    Examples:
        honk notes edit meeting.md
        honk notes edit --idle 60 notes.md
        honk notes edit --prompt custom.txt todo.md
    """
    # Load custom prompt if specified
    prompt_template = None
    if prompt:
        if not prompt.exists():
            print_error(f"Prompt file not found: {prompt}")
            raise typer.Exit(1)
        prompt_template = prompt.read_text()
    
    # Create config
    config = NotesConfig(
        file_path=file,
        idle_timeout=idle_timeout,
        auto_save=not no_auto_save,
        prompt_template=prompt_template,
    )
    
    # Run app
    app = StreamingNotesApp(config)
    app.run()

@notes_app.command()
def organize(
    file: Path = typer.Argument(..., help="File to organize"),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file (default: overwrite input)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print result without saving"
    ),
):
    """
    Organize notes file with AI (non-interactive).
    
    Examples:
        honk notes organize meeting.md
        honk notes organize notes.md -o organized.md
        honk notes organize --dry-run todo.md
    """
    import asyncio
    from .organizer import AIOrganizer
    from honk.ui import console
    
    if not file.exists():
        print_error(f"File not found: {file}")
        raise typer.Exit(1)
    
    content = file.read_text()
    organizer = AIOrganizer()
    
    # Run organization
    try:
        organized = asyncio.run(organizer.organize(content))
        
        if dry_run:
            console.print(organized)
        else:
            output_path = output or file
            output_path.write_text(organized)
            print_success(f"✓ Organized notes saved to {output_path}")
    
    except Exception as e:
        print_error(f"Organization failed: {e}")
        raise typer.Exit(1)

@notes_app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration"
    ),
):
    """
    Manage notes configuration.
    """
    from honk.ui import console
    
    config = NotesConfig.load()
    
    if show:
        console.print(config)
    else:
        typer.echo("Configuration management coming soon!")
```

---

## Integration with Honk CLI

**In `src/honk/cli.py`:**

```python
from .notes.cli import notes_app

app.add_typer(
    notes_app,
    name="notes",
    help="AI-assisted note-taking"
)
```

---

## Shared Components Usage

| Component | Location | Usage in Notes |
|-----------|----------|---------------|
| `console` | `honk.ui` | Rich terminal output |
| `print_success/error/info` | `honk.ui.theme` | CLI feedback messages |
| `HONK_THEME` | `honk.ui.theme` | Consistent styling |
| `ensure_gh_auth` | `honk.auth` | Verify Copilot access |
| Command registry | `honk.registry` | Register commands |

---

## Testing Strategy

### Unit Tests

```python
# tests/notes/test_organizer.py
import pytest
from honk.notes.organizer import AIOrganizer

@pytest.mark.asyncio
async def test_organizer_basic():
    organizer = AIOrganizer()
    content = "- buy milk\n- call john\n- review code"
    result = await organizer.organize(content)
    assert "##" in result  # Should have sections
    assert len(result) > len(content)  # Should be organized

# tests/notes/test_auto_save.py
import pytest
from honk.notes.auto_save import AutoSaver

@pytest.mark.asyncio
async def test_debounced_save(tmp_path):
    file = tmp_path / "test.md"
    saver = AutoSaver(file, debounce_seconds=0.1)
    
    await saver.schedule_save("draft 1")
    await saver.schedule_save("draft 2")  # Should cancel first
    await asyncio.sleep(0.2)
    
    assert file.read_text() == "draft 2"
```

### Integration Tests

```python
# tests/notes/test_app.py
from textual.pilot import Pilot
from honk.notes.app import StreamingNotesApp
from honk.notes.config import NotesConfig

async def test_app_basic_editing():
    config = NotesConfig()
    app = StreamingNotesApp(config)
    
    async with app.run_test() as pilot:
        # Type some text
        await pilot.press("h", "e", "l", "l", "o")
        
        editor = app.query_one("#editor")
        assert "hello" in editor.text
```

---

## Deployment Checklist

- [ ] All components implemented
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] CLI commands registered
- [ ] Documentation written
- [ ] Error handling robust
- [ ] Performance validated
- [ ] GitHub Copilot CLI access verified

---

## Future Enhancements (Phase 2)

1. **Split-view mode** (`--split` flag)
2. **Template system** (meeting notes, daily notes, etc.)
3. **Search functionality** (full-text search)
4. **Version history** (track organization iterations)
5. **Export formats** (PDF, HTML)
6. **Collaboration** (real-time multi-user)
7. **Voice input** (transcribe + organize)
8. **Integration hooks** (GitHub issues, calendars)

---

## Success Metrics

**MVP Success Criteria**:
- ✅ Editor loads and saves files correctly
- ✅ Idle detection triggers after 30s
- ✅ AI organization improves note structure
- ✅ No flickering or visual artifacts
- ✅ Auto-save prevents data loss
- ✅ Manual organization works on-demand
- ✅ Error handling is graceful

**User Success Criteria**:
- Users can take quick notes without friction
- AI organization is helpful (not annoying)
- Performance feels instant (<100ms response)
- No data loss under any conditions
- Clear feedback at every stage

---

## Implementation Timeline

**Week 1** (Foundation):
- Day 1-2: Config, widgets, app shell
- Day 3-4: AI organizer integration
- Day 5: CLI commands

**Week 2** (Polish):
- Day 6-7: Auto-save, error handling
- Day 8-9: Testing, bug fixes
- Day 10: Documentation, release

**Total Estimate**: 10 days for full implementation

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Copilot CLI unavailable | Graceful fallback, clear error |
| Network latency | Show progress, allow cancellation |
| Large files slow | Add file size warnings |
| Data loss | Aggressive auto-save, backup |
| Bad AI output | Allow manual undo/revert |

---

## Conclusion

This specification provides a complete blueprint for implementing Honk Notes. The single-pane design prioritizes simplicity and usability while leveraging Textual's reactive architecture for a polished, professional terminal UI experience.

**Next Step**: Implementation via planloop! 🚀
