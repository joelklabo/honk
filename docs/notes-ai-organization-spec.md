# Honk Notes AI Organization Feature - Technical Specification

**Created**: 2025-11-18  
**Status**: Proposal Phase  
**Research Time**: 90 minutes  
**Searches Conducted**: 6

---

## Executive Summary

This spec defines how Honk Notes will integrate AI-assisted text organization with **graceful streaming animations**. Users trigger organization **manually with Ctrl+O** (already works!), the editor sends content to GitHub Copilot CLI with a custom prompt, receives streamed organized text, and **incrementally animates the changes** in the TextArea.

**Key Goals:**
- ✅ Manual trigger with Ctrl+O (no annoying idle timeouts!)
- ✅ Auto-reload on file changes (external editor support)
- ✅ Stream responses from Copilot CLI
- ✅ Gracefully animate updates in real-time
- ✅ No jarring full-text replacements
- ✅ Allow custom organization prompts
- ✅ Handle errors gracefully

---

## 🤖 AI Agent Integration Points

**Critical for AI agent usability**: Honk Notes must be AI-agent-friendly to avoid situations where agents get stuck in text editors (e.g., git commit editors).

### Non-Blocking API Design

```python
# AI agents can use programmatic API instead of interactive UI
from honk.notes import NotesAPI

# Non-blocking operations
api = NotesAPI()

# Get current buffer content
content = await api.get_content("notes.md")

# Set content without opening UI
await api.set_content("notes.md", new_content)

# Organize content programmatically
organized = await api.organize(content, prompt=custom_prompt)

# Check if file is being edited (lock detection)
is_locked = await api.is_locked("notes.md")
```

### Command-Line Integration

```bash
# AI agents can use CLI for scripting
honk notes get notes.md           # Print content to stdout
honk notes set notes.md "content" # Write content non-interactively
honk notes organize notes.md      # Organize and write back
honk notes status notes.md        # Check if locked/being edited

# Exit codes for agent scripting
# 0 = success
# 1 = file not found
# 2 = file locked (being edited)
# 3 = organization failed
```

### Agent-Friendly Features

**1. Lock Detection**: Agents can check if file is being edited before modifying
**2. Non-Blocking Operations**: All operations have async API
**3. Status Queries**: Get buffer state without opening UI
**4. Batch Operations**: Organize multiple files programmatically
**5. Progress Reporting**: Agents can monitor long operations
**6. Graceful Timeouts**: Operations fail cleanly instead of hanging

### Use Cases for AI Agents

**Use Case 1: Auto-Organization Pipeline**
```python
# Agent workflow: Edit → Organize → Commit
await notes_api.set_content("notes.md", new_notes)
organized = await notes_api.organize("notes.md")
if organized.success:
    await git.commit("Updated organized notes")
```

**Use Case 2: Batch Processing**
```python
# Organize all notes in directory
for note_file in Path("notes").glob("*.md"):
    if not await notes_api.is_locked(note_file):
        await notes_api.organize(note_file)
```

**Use Case 3: Integration with Other Tools**
```python
# Extract content, process with other tools, write back
content = await notes_api.get_content("research.md")
enhanced = await research_agent.enhance(content)
await notes_api.set_content("research.md", enhanced)
```

---

## 🎯 Two Proposals

Based on research into Textual animations, asyncio streaming, diff algorithms, and LLM streaming best practices, here are **two architectural approaches**:

---

# Proposal 1: Diff-Based Incremental Animation

**Philosophy**: Compute a semantic diff between original and organized text, then apply changes incrementally with visual feedback.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    StreamingNotesApp                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ IdleDetector │───▶│ AIOrganizer  │───▶│ DiffAnimator │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         │                    │                    │         │
│    [Debounce]          [Stream LLM]        [Animate Diff]  │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              StreamingTextArea                       │  │
│  │  - Apply incremental patches                         │  │
│  │  - Highlight changed regions                         │  │
│  │  - Smooth transitions                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User presses Ctrl+O → Call Copilot CLI with prompt
                                           ↓
                                    Stream response chunks
                                           ↓
                                    Buffer complete response
                                           ↓
                                    Compute diff (original ↔ organized)
                                           ↓
                                    Apply patches incrementally
                                           ↓
                                    Animate each change region
                                           ↓
                                    Complete ✓

Separate Flow:
File changes externally → Auto-reload → Show notification
```

## Implementation Details

### 1. FileWatcher (Auto-Reload on External Changes)

**File**: `src/honk/notes/file_watcher.py`

```python
import asyncio
from pathlib import Path
from typing import Optional, Callable
from watchfiles import awatch

class FileWatcher:
    """Watches for external file changes and triggers reload."""
    
    def __init__(self, file_path: Path, callback: Optional[Callable] = None):
        self.file_path = file_path
        self.callback = callback
        self._watch_task: Optional[asyncio.Task] = None
        self._last_mtime = None
    
    async def start(self):
        """Start watching file for changes."""
        self._watch_task = asyncio.create_task(self._watch_loop())
    
    async def _watch_loop(self):
        """Watch for file changes and trigger callback."""
        async for changes in awatch(self.file_path.parent):
            for change_type, changed_path in changes:
                if Path(changed_path) == self.file_path:
                    # File changed externally
                    if self.callback:
                        await self.callback()
    
    def stop(self):
        """Stop watching file."""
        if self._watch_task:
            self._watch_task.cancel()
```

**Integration**:
```python
# In StreamingNotesApp
async def on_mount(self):
    if self.config.file_path:
        self.file_watcher = FileWatcher(
            self.config.file_path,
            callback=self._on_file_changed_externally
        )
        await self.file_watcher.start()

async def _on_file_changed_externally(self):
    """Reload file content when changed externally."""
    if not self.is_dirty:
        # No unsaved changes, safe to reload
        editor = self.query_one("#editor")
        new_content = self.config.file_path.read_text()
        editor.text = new_content
        self.notify("📄 File reloaded (changed externally)", timeout=2)
    else:
        # Has unsaved changes, prompt user
        self.notify("⚠️  File changed externally. Save or discard changes.", 
                   severity="warning", timeout=5)
```

### 2. AIOrganizer (Streaming LLM Calls)

**File**: `src/honk/notes/organizer.py`

```python
import asyncio
from typing import AsyncIterator, Tuple

class AIOrganizer:
    """Streams AI-organized text from Copilot CLI."""
    
    def __init__(self, prompt_template: Optional[str] = None):
        self.prompt_template = prompt_template or self._default_prompt()
    
    def _default_prompt(self) -> str:
        return """You are a note organization assistant. 
        
Organize the following notes to be clearer and better structured:
- Group related items together
- Create clear headings and sections
- Fix formatting inconsistencies
- Preserve all information
- Return ONLY the organized note content, no explanation

Notes:
{content}

Organized notes:"""
    
    async def organize_stream(
        self, 
        content: str
    ) -> AsyncIterator[Tuple[str, float]]:
        """Stream organized content from Copilot CLI.
        
        Yields:
            (partial_text, progress) tuples
        """
        prompt = self.prompt_template.format(content=content)
        
        # Invoke Copilot CLI with streaming
        process = await asyncio.create_subprocess_exec(
            'copilot', 'chat',
            '--prompt', prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        buffer = ""
        total_size_estimate = len(content) * 1.2  # Estimate organized size
        
        while True:
            chunk = await process.stdout.read(100)  # Read in chunks
            if not chunk:
                break
            
            chunk_str = chunk.decode('utf-8', errors='ignore')
            buffer += chunk_str
            
            progress = min(len(buffer) / total_size_estimate, 0.99)
            yield buffer, progress
        
        await process.wait()
        yield buffer, 1.0  # Final complete text
```

### 3. DiffAnimator (Incremental Patch Application)

**File**: `src/honk/notes/diff_animator.py`

```python
from diff_match_patch import diff_match_patch
from typing import List, Tuple
import asyncio

class DiffAnimator:
    """Applies text diffs with visual animation."""
    
    def __init__(self, text_area):
        self.text_area = text_area
        self.dmp = diff_match_patch()
    
    async def apply_animated_diff(
        self, 
        original: str, 
        organized: str,
        animation_speed: float = 0.05  # seconds per change
    ):
        """Apply diff incrementally with animations.
        
        Args:
            original: Current text
            organized: Target organized text
            animation_speed: Seconds to pause between changes
        """
        # Compute diff
        diffs = self.dmp.diff_main(original, organized)
        self.dmp.diff_cleanupSemantic(diffs)  # Clean up for better UX
        
        # Convert to patches for granular application
        patches = self.dmp.patch_make(original, diffs)
        
        # Apply patches incrementally
        current_text = original
        current_offset = 0
        
        for patch in patches:
            # Compute patch boundaries in current text
            start = patch.start1 + current_offset
            
            # Highlight region about to change (yellow background)
            await self._highlight_region(start, start + patch.length1)
            await asyncio.sleep(animation_speed)
            
            # Apply the patch
            result_text, applied = self.dmp.patch_apply([patch], current_text)
            
            if applied[0]:
                current_text = result_text
                self.text_area.text = current_text
                
                # Flash green to show completion
                await self._flash_region(start, start + patch.length2, "green")
                await asyncio.sleep(animation_speed)
            
            # Update offset for next patch
            current_offset += (patch.length2 - patch.length1)
        
        # Clear all highlights
        await self._clear_highlights()
    
    async def _highlight_region(self, start: int, end: int, color: str = "yellow"):
        """Highlight text region (visual feedback)."""
        # Use Textual's style system to highlight
        # This is pseudo-code - actual implementation depends on TextArea API
        pass
    
    async def _flash_region(self, start: int, end: int, color: str = "green"):
        """Flash a region briefly to indicate change."""
        await self._highlight_region(start, end, color)
        await asyncio.sleep(0.2)
        await self._clear_highlights()
    
    async def _clear_highlights(self):
        """Remove all highlights."""
        pass
```

### 4. Integration into StreamingNotesApp

**File**: `src/honk/notes/app.py` (modifications)

```python
class StreamingNotesApp(App):
    def __init__(self, config: NotesConfig):
        super().__init__()
        self.config = config
        self.organizer = AIOrganizer(config.prompt_template)
        self.diff_animator = None  # Created after editor widget exists
        self.idle_detector = IdleDetector(
            timeout=config.idle_timeout,
            callback=self._on_idle_reached
        )
    
    async def on_mount(self):
        editor = self.query_one("#editor")
        self.diff_animator = DiffAnimator(editor)
    
    def on_text_area_changed(self, event):
        """Reset idle timer on every keystroke."""
        self.idle_detector.reset()
    
    async def _on_idle_reached(self):
        """Triggered when user stops typing."""
        if self.organizing:
            return  # Already organizing
        
        await self._organize_content()
    
    async def _organize_content(self):
        """Main organization flow."""
        self.organizing = True
        editor = self.query_one("#editor")
        original_text = editor.text
        
        # Show processing overlay
        overlay = self.query_one("#processing")
        overlay.show("🤖 AI is organizing your notes...")
        
        try:
            # Stream organized text
            organized_text = ""
            async for partial, progress in self.organizer.organize_stream(original_text):
                organized_text = partial
                overlay.update_progress(progress, f"Organizing... {int(progress*100)}%")
            
            # Apply diff with animation
            await self.diff_animator.apply_animated_diff(original_text, organized_text)
            
            overlay.update_progress(1.0, "✓ Done!")
            await asyncio.sleep(0.5)
        
        except Exception as e:
            self.notify(f"Organization failed: {e}", severity="error")
        
        finally:
            overlay.hide()
            self.organizing = False
```

## Pros & Cons

### ✅ Pros

1. **Smooth Visual Feedback**: Users see exactly what changed with highlights
2. **Semantic Diffs**: Only changes meaningful sections, not entire text
3. **Predictable**: Diff-based approach is deterministic
4. **Error Recovery**: Can roll back if AI produces bad output
5. **Educational**: Users learn what AI changed

### ❌ Cons

1. **Complexity**: Requires diff library and custom animation logic
2. **Performance**: Large documents may have slow diff computation
3. **Wait Time**: User waits for full response before seeing changes
4. **Highlight Limitations**: TextArea may not support rich inline highlighting
5. **Memory**: Needs to buffer full response before applying

## Dependencies

```toml
# pyproject.toml additions
[project.dependencies]
diff-match-patch = "^20241021"  # For semantic diff
watchfiles = "^0.21.0"          # For file watching
```

---

# Proposal 2: True Streaming Character-by-Character

**Philosophy**: Stream organized text character-by-character as it arrives from the LLM, replacing content in real-time like a "type-writer" effect.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    StreamingNotesApp                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ IdleDetector │───▶│ AIOrganizer  │───▶│StreamRenderer│ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         │                    │                    │         │
│    [Debounce]          [Stream LLM]     [Typewriter Effect] │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              StreamingTextArea                       │  │
│  │  - Replace text incrementally                        │  │
│  │  - Show cursor at update position                    │  │
│  │  - Smooth character reveal                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User presses Ctrl+O → Call Copilot CLI with prompt
                                           ↓
                                    Stream response chunks
                                           ↓
                                    For each chunk received:
                                      - Append to buffer
                                      - Update TextArea immediately
                                      - Show typing animation
                                           ↓
                                    Complete ✓

Separate Flow:
File changes externally → Auto-reload → Show notification
```

## Implementation Details

### 1. StreamRenderer (Real-Time Text Updates)

**File**: `src/honk/notes/stream_renderer.py`

```python
import asyncio
from typing import AsyncIterator

class StreamRenderer:
    """Renders streaming text updates with typewriter effect."""
    
    def __init__(self, text_area, animation_speed: float = 0.02):
        self.text_area = text_area
        self.animation_speed = animation_speed  # seconds per character
    
    async def render_stream(
        self, 
        stream: AsyncIterator[Tuple[str, float]],
        start_position: int = 0
    ):
        """Render streaming text updates.
        
        Args:
            stream: Async iterator yielding (partial_text, progress)
            start_position: Character position to start replacing from
        """
        previous_text = ""
        
        async for partial_text, progress in stream:
            # Only render new characters since last update
            new_chars = partial_text[len(previous_text):]
            
            if new_chars:
                # Update text area incrementally
                current_content = self.text_area.text[:start_position]
                self.text_area.text = current_content + partial_text
                
                # Optional: Add small delay for typewriter effect
                if len(new_chars) < 100:  # Only for small updates
                    await asyncio.sleep(self.animation_speed * len(new_chars))
            
            previous_text = partial_text
        
        # Ensure final state is set
        self.text_area.text = self.text_area.text[:start_position] + previous_text
```

### 2. Modified AIOrganizer (Chunk Streaming)

**File**: `src/honk/notes/organizer.py`

```python
class AIOrganizer:
    """Streams AI-organized text from Copilot CLI."""
    
    async def organize_stream(
        self, 
        content: str
    ) -> AsyncIterator[Tuple[str, float]]:
        """Stream organized content chunk-by-chunk as it arrives.
        
        Yields:
            (partial_text, progress) tuples immediately as chunks arrive
        """
        prompt = self.prompt_template.format(content=content)
        
        # Invoke Copilot CLI with streaming
        process = await asyncio.create_subprocess_exec(
            'copilot', 'chat',
            '--prompt', prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        buffer = ""
        chunk_count = 0
        
        # Read and yield immediately - true streaming
        while True:
            # Read small chunks for responsive updates
            chunk = await process.stdout.read(50)
            if not chunk:
                break
            
            chunk_str = chunk.decode('utf-8', errors='ignore')
            buffer += chunk_str
            chunk_count += 1
            
            # Estimate progress (rough heuristic)
            progress = min(0.95, chunk_count / 200)
            
            # Yield immediately - no buffering!
            yield buffer, progress
        
        await process.wait()
        yield buffer, 1.0
```

### 3. Integration into StreamingNotesApp

**File**: `src/honk/notes/app.py` (modifications)

```python
class StreamingNotesApp(App):
    def __init__(self, config: NotesConfig):
        super().__init__()
        self.config = config
        self.organizer = AIOrganizer(config.prompt_template)
        self.stream_renderer = None
        self.idle_detector = IdleDetector(
            timeout=config.idle_timeout,
            callback=self._on_idle_reached
        )
    
    async def on_mount(self):
        editor = self.query_one("#editor")
        self.stream_renderer = StreamRenderer(
            editor, 
            animation_speed=0.01  # Fast typewriter effect
        )
    
    async def _organize_content(self):
        """Main organization flow with streaming."""
        self.organizing = True
        editor = self.query_one("#editor")
        
        # Show processing overlay
        overlay = self.query_one("#processing")
        overlay.show("🤖 AI is organizing your notes...")
        
        try:
            # Get streaming iterator
            stream = self.organizer.organize_stream(editor.text)
            
            # Render stream in real-time
            # Clear editor first, then stream new content
            start_pos = 0
            editor.text = ""
            
            async for partial, progress in stream:
                # Update text directly - no diffing
                editor.text = partial
                overlay.update_progress(progress, "Organizing...")
                
                # Small delay for visual smoothness
                await asyncio.sleep(0.02)
            
            overlay.update_progress(1.0, "✓ Done!")
            await asyncio.sleep(0.5)
        
        except Exception as e:
            self.notify(f"Organization failed: {e}", severity="error")
        
        finally:
            overlay.hide()
            self.organizing = False
```

### 4. Enhanced Visuals (Optional)

**Add a streaming cursor indicator:**

```python
class StreamingOverlay(Widget):
    """Shows a blinking cursor during streaming."""
    
    def __init__(self):
        super().__init__()
        self.streaming = False
    
    def compose(self):
        yield Static("▊", classes="streaming-cursor")
    
    async def start_streaming(self):
        self.streaming = True
        cursor = self.query_one(".streaming-cursor")
        
        while self.streaming:
            cursor.styles.animate("opacity", value=0.0, duration=0.5)
            await asyncio.sleep(0.5)
            cursor.styles.animate("opacity", value=1.0, duration=0.5)
            await asyncio.sleep(0.5)
    
    def stop_streaming(self):
        self.streaming = False
```

## Pros & Cons

### ✅ Pros

1. **Immediate Feedback**: Users see results as they arrive
2. **Simpler Code**: No diff computation needed
3. **Feels Responsive**: Like watching AI "think"
4. **Lower Memory**: No need to buffer full response
5. **Engaging UX**: Typewriter effect is satisfying

### ❌ Cons

1. **Jarring for Large Changes**: Entire text replaced
2. **No Undo Context**: Hard to see what specifically changed
3. **Disorienting**: User loses reading position
4. **Can't Cancel Mid-Stream**: Partial results may be incomplete
5. **Less Educational**: Don't see diff, just result

## Dependencies

```toml
# pyproject.toml additions
[project.dependencies]
watchfiles = "^0.21.0"  # For file watching
# That's it! Much simpler
```

---

## Comparison Matrix

| Aspect | Proposal 1: Diff-Based | Proposal 2: True Streaming |
|--------|------------------------|----------------------------|
| **Visual Feedback** | ✅ Highlights changed regions | ⚠️ Replaces entire text |
| **User Understanding** | ✅ Clear what changed | ❌ No diff visibility |
| **Implementation Complexity** | ❌ High (diff + animation) | ✅ Low (direct streaming) |
| **Streaming Latency** | ❌ Wait for full response | ✅ Immediate feedback |
| **Memory Usage** | ❌ Buffer full response | ✅ Minimal buffering |
| **Error Recovery** | ✅ Can rollback | ⚠️ Harder to undo |
| **UX Polish** | ✅ Feels professional | ✅ Feels engaging |
| **Performance (Large Docs)** | ⚠️ Diff computation slow | ✅ Fast streaming |
| **Cursor Position** | ✅ Preserved (mostly) | ❌ Lost during update |
| **Dependencies** | ⚠️ diff-match-patch | ✅ Minimal |
| **Best For** | Precise edits, small changes | Complete reorganization |

---

## 🎯 Recommendation

### **Hybrid Approach** (Best of Both)

Combine both proposals for maximum UX:

1. **Use Proposal 2 (Streaming) by default** for:
   - Manual trigger with Ctrl+O (user-controlled!)
   - Large reorganizations (full rewrites)
   - Engaging visual experience

2. **Add Proposal 1 (Diff) as enhancement** for:
   - Post-stream "show changes" mode
   - Undo functionality (show what changed)
   - A/B comparison view (original vs organized)

3. **Add File Watching** for:
   - Auto-reload when file changes externally
   - Support editing in external editor
   - Conflict detection (unsaved changes)

### Implementation Phases

**Phase 1: Core Streaming** (1-2 weeks)
- ✅ Manual trigger with Ctrl+O (already works!)
- ✅ FileWatcher for external changes
- ✅ AIOrganizer with Copilot CLI streaming
- ✅ Basic text replacement
- ✅ Progress overlay

**Phase 2: Visual Polish** (1 week)
- ✅ Typewriter effect smoothing
- ✅ Streaming cursor indicator
- ✅ Better progress estimation

**Phase 3: Diff Enhancement** (1-2 weeks)
- ✅ Add diff computation
- ✅ "Show changes" button
- ✅ Undo to original
- ✅ Highlight mode toggle

**Phase 4: Advanced Features** (1 week)
- ✅ Custom prompts UI
- ✅ Organization history
- ✅ Cancel mid-stream
- ✅ Partial acceptance (accept some changes, reject others)

---

## API Design for Honk Integration

### CLI Command

```bash
# Basic usage
honk notes edit myfile.md

# Custom organization prompt
honk notes edit myfile.md --prompt organize_prompt.txt

# Disable file watching (for performance)
honk notes edit myfile.md --no-watch

# Manual organization from CLI
honk notes organize myfile.md

# Organization in place: Ctrl+O while editing
```

### Configuration

**File**: `~/.config/honk/notes.toml`

```toml
[organization]
enabled = true
animation_speed = 0.02  # seconds per character
show_diff = true  # show changes after organizing

[file_watching]
enabled = true
auto_reload = true  # reload on external changes
prompt_on_conflict = true  # prompt if unsaved changes

[prompts]
default = """You are a note organization assistant..."""
custom_prompts_dir = "~/.config/honk/prompts/"
```

### Python API

```python
from honk.notes import StreamingNotesApp, NotesConfig

# Create config
config = NotesConfig(
    file_path=Path("notes.md"),
    watch_file=True,
    prompt_template=custom_prompt
)

# Run app (Ctrl+O to organize)
app = StreamingNotesApp(config)
app.run()

# Programmatic organization
from honk.notes import AIOrganizer

organizer = AIOrganizer(prompt)
async for partial, progress in organizer.organize_stream(content):
    print(f"Progress: {progress*100:.0f}%")
    print(partial)

# File watching
from honk.notes import FileWatcher

watcher = FileWatcher(Path("notes.md"), callback=on_file_changed)
await watcher.start()
```

---

## Shared Components to Leverage

### From Honk Core

1. **`honk.ui.ProcessingOverlay`**: Already has progress animation
2. **`honk.ui.LoadingIndicator`**: Can show streaming status
3. **`honk.ui.print_error/print_success`**: For error/success messages
4. **`honk.config`**: Configuration management patterns
5. **Honk's design system**: Colors, styles, animations

### New Shared Components to Create

1. **`honk.streaming.StreamingSubprocess`**: Reusable subprocess streaming
2. **`honk.animation.TypewriterEffect`**: Reusable typewriter animation
3. **`honk.text.DiffHighlighter`**: Diff visualization widget
4. **`honk.files.FileWatcher`**: General-purpose file watching utility
5. **`honk.notes.NotesAPI`**: Non-blocking API for agent integration

---

## AI Agent Integration Architecture

### NotesAPI Implementation

**File**: `src/honk/notes/api.py`

```python
"""Non-blocking API for AI agent integration."""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class OrganizationResult:
    """Result of organization operation."""
    success: bool
    content: str
    error: Optional[str] = None
    duration_seconds: float = 0.0


class NotesAPI:
    """Non-blocking API for programmatic notes manipulation."""
    
    def __init__(self):
        self._locks: Dict[Path, asyncio.Lock] = {}
    
    async def get_content(self, file_path: str | Path) -> str:
        """Get file content without opening UI.
        
        Args:
            file_path: Path to notes file
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is locked
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if await self.is_locked(path):
            raise PermissionError(f"File is locked (being edited): {path}")
        
        return path.read_text()
    
    async def set_content(
        self, 
        file_path: str | Path, 
        content: str,
        create: bool = False
    ) -> None:
        """Set file content without opening UI.
        
        Args:
            file_path: Path to notes file
            content: New content to write
            create: Create file if it doesn't exist
            
        Raises:
            FileNotFoundError: If file doesn't exist and create=False
            PermissionError: If file is locked
        """
        path = Path(file_path)
        
        if not create and not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if await self.is_locked(path):
            raise PermissionError(f"File is locked (being edited): {path}")
        
        path.write_text(content)
    
    async def organize(
        self,
        file_path: str | Path,
        prompt: Optional[str] = None,
        timeout: float = 60.0
    ) -> OrganizationResult:
        """Organize file content using AI.
        
        Args:
            file_path: Path to notes file
            prompt: Custom organization prompt (optional)
            timeout: Maximum time to wait for organization
            
        Returns:
            OrganizationResult with organized content
        """
        import time
        from .organizer import AIOrganizer
        
        start_time = time.time()
        path = Path(file_path)
        
        try:
            # Get current content
            content = await self.get_content(path)
            
            # Organize
            organizer = AIOrganizer(prompt)
            organized_content = ""
            
            async with asyncio.timeout(timeout):
                async for partial, progress in organizer.organize_stream(content):
                    organized_content = partial
            
            # Write back
            await self.set_content(path, organized_content)
            
            duration = time.time() - start_time
            
            return OrganizationResult(
                success=True,
                content=organized_content,
                duration_seconds=duration
            )
        
        except Exception as e:
            duration = time.time() - start_time
            return OrganizationResult(
                success=False,
                content="",
                error=str(e),
                duration_seconds=duration
            )
    
    async def is_locked(self, file_path: str | Path) -> bool:
        """Check if file is being edited (locked).
        
        Args:
            file_path: Path to notes file
            
        Returns:
            True if file is locked, False otherwise
        """
        path = Path(file_path)
        lock = self._locks.get(path)
        return lock is not None and lock.locked()
    
    async def get_status(self, file_path: str | Path) -> Dict[str, Any]:
        """Get file status.
        
        Args:
            file_path: Path to notes file
            
        Returns:
            Status dictionary with metadata
        """
        path = Path(file_path)
        
        return {
            "exists": path.exists(),
            "locked": await self.is_locked(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "modified": path.stat().st_mtime if path.exists() else None,
        }
```

### CLI Integration

**File**: `src/honk/notes/cli.py` (additions)

```python
@notes_app.command()
def get(file_path: Path):
    """Get notes content (non-interactive, agent-friendly)."""
    try:
        api = NotesAPI()
        content = asyncio.run(api.get_content(file_path))
        print(content)
        sys.exit(0)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: File is locked: {file_path}", file=sys.stderr)
        sys.exit(2)


@notes_app.command()
def set(
    file_path: Path,
    content: str = typer.Argument(..., help="Content to write"),
    create: bool = typer.Option(False, "--create", help="Create if doesn't exist")
):
    """Set notes content (non-interactive, agent-friendly)."""
    try:
        api = NotesAPI()
        asyncio.run(api.set_content(file_path, content, create=create))
        sys.exit(0)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: File is locked: {file_path}", file=sys.stderr)
        sys.exit(2)


@notes_app.command()
def status(file_path: Path):
    """Get file status (agent-friendly)."""
    try:
        api = NotesAPI()
        status_dict = asyncio.run(api.get_status(file_path))
        
        # JSON output for easy parsing
        import json
        print(json.dumps(status_dict, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### Agent Usage Examples

**Example 1: Safe Content Update**
```python
# Agent checks lock before updating
api = NotesAPI()

if not await api.is_locked("notes.md"):
    await api.set_content("notes.md", new_content)
else:
    print("File is being edited, skipping update")
```

**Example 2: Batch Organization**
```python
# Organize all notes, skip locked files
from pathlib import Path

api = NotesAPI()
notes_dir = Path("~/notes").expanduser()

for note_file in notes_dir.glob("*.md"):
    if not await api.is_locked(note_file):
        result = await api.organize(note_file)
        if result.success:
            print(f"✓ Organized {note_file.name} in {result.duration_seconds:.1f}s")
        else:
            print(f"✗ Failed {note_file.name}: {result.error}")
    else:
        print(f"⊘ Skipped {note_file.name} (locked)")
```

**Example 3: Shell Script Integration**
```bash
#!/bin/bash
# organize-all-notes.sh

for file in ~/notes/*.md; do
    # Check status first
    status=$(honk notes status "$file")
    locked=$(echo "$status" | jq -r '.locked')
    
    if [ "$locked" = "false" ]; then
        echo "Organizing $file..."
        if honk notes organize "$file"; then
            echo "✓ Done"
        else
            echo "✗ Failed"
        fi
    else
        echo "⊘ Skipped $file (locked)"
    fi
done
```

---

## Testing Strategy

### Unit Tests

```python
# tests/notes/test_idle_detector.py
async def test_idle_detector_triggers_after_timeout():
    called = False
    async def callback():
        nonlocal called
        called = True
    
    detector = IdleDetector(timeout=0.1, callback=callback)
    detector.reset()
    await asyncio.sleep(0.15)
    assert called

# tests/notes/test_organizer.py
async def test_organizer_streams_content():
    organizer = AIOrganizer()
    chunks = []
    
    async for partial, progress in organizer.organize_stream("test"):
        chunks.append((partial, progress))
    
    assert len(chunks) > 0
    assert chunks[-1][1] == 1.0  # Final progress is 100%

# tests/notes/test_diff_animator.py
async def test_diff_animator_applies_changes():
    text_area = MockTextArea()
    animator = DiffAnimator(text_area)
    
    await animator.apply_animated_diff("old text", "new text")
    assert text_area.text == "new text"
```

### Integration Tests

```python
# tests/notes/test_integration.py
async def test_full_organization_flow():
    """Test from idle trigger to final organized text."""
    config = NotesConfig(idle_timeout=0.1)
    app = StreamingNotesApp(config)
    
    # Simulate user typing
    editor = app.query_one("#editor")
    editor.text = "Test notes\nTo organize"
    
    # Trigger change
    editor.post_message(TextArea.Changed(editor))
    
    # Wait for idle
    await asyncio.sleep(0.15)
    
    # Should trigger organization
    assert app.organizing
    
    # Wait for completion
    await asyncio.sleep(2.0)
    
    assert not app.organizing
    assert editor.text != "Test notes\nTo organize"
```

### Manual Testing Checklist

- [ ] Press Ctrl+O, verify organization triggers
- [ ] Organization shows progress overlay
- [ ] Text updates smoothly (no flicker)
- [ ] Can continue typing after organization
- [ ] Custom prompts work correctly
- [ ] Error handling displays properly
- [ ] Cancel organization mid-stream
- [ ] Large documents (>10KB) organize smoothly
- [ ] Network errors handled gracefully
- [ ] External file changes trigger reload
- [ ] Conflict detection works (unsaved changes)
- [ ] File watching can be disabled

---

## Production Considerations

### Performance

- **Chunk Size**: 50-100 bytes optimal for balance
- **Progress Estimation**: Use heuristics (chunk count, time elapsed)
- **Large Documents**: Consider showing "This may take a minute..." warning
- **Background Processing**: Don't block UI thread

### Error Handling

```python
class OrganizationError(Exception):
    """Raised when organization fails."""
    pass

class CopilotUnavailableError(OrganizationError):
    """Raised when Copilot CLI not found."""
    pass

class StreamInterruptedError(OrganizationError):
    """Raised when stream is interrupted."""
    pass
```

### Rate Limiting

- **Copilot API**: Respect rate limits
- **Debounce**: Don't trigger on every keystroke
- **Cool down**: Wait 5s minimum between organization attempts

### Fallbacks

```python
# If Copilot unavailable, offer alternatives:
# 1. Local LLM (via ollama)
# 2. Rule-based organization (headings, bullet points)
# 3. Graceful degradation (just auto-save)
```

---

## Open Questions

1. **Should we show original during streaming?**
   - Option A: Replace text immediately (Proposal 2)
   - Option B: Show side-by-side preview
   - Option C: Show in modal dialog

2. **What if user types during organization?**
   - Option A: Cancel organization (CHOSEN - manual trigger means user controls timing)
   - Option B: Queue changes to apply after
   - Option C: Block typing (not recommended)

**Decision**: Option A. Since Ctrl+O is manual, users won't trigger it while typing.

3. **How to handle very long responses?**
   - Option A: Stream all (may be slow)
   - Option B: Truncate with warning
   - Option C: Chunk into sections

4. **Undo behavior?**
   - Option A: Ctrl+Z undoes entire organization
   - Option B: Keep organization history
   - Option C: Show diff, let user accept/reject

---

## Success Criteria

✅ **Functional:**
- Organization triggers on Ctrl+O
- File reloads on external changes
- Copilot CLI integration works
- Text streams smoothly
- Errors handled gracefully

✅ **Performance:**
- Organization completes in <30s for typical notes
- No UI freezing during streaming
- <100MB memory usage

✅ **UX:**
- Users understand what's happening
- Animation is smooth and polished
- Can continue working after organization
- No data loss on errors

✅ **Code Quality:**
- Test coverage >80%
- Type hints throughout
- Documentation complete
- Follows Honk patterns

---

## Next Steps

1. **Review Proposals**: Choose Diff-Based, True Streaming, or Hybrid
2. **Prototype**: Build minimal version of chosen approach
3. **User Testing**: Get feedback on UX
4. **Iterate**: Refine based on feedback
5. **Implement**: Full feature with tests
6. **Document**: User guide and API docs

---

## References

### Research Sources

1. **Textual Animation**: https://textual.textualize.io/guide/animation/
2. **Textual TextArea**: https://textual.textualize.io/widgets/text_area/
3. **Diff Match Patch**: https://pypi.org/project/diff-match-patch/
4. **LLM Streaming Best Practices**: https://developer.chrome.com/docs/ai/render-llm-responses
5. **Python Asyncio Patterns**: https://docs.python.org/3/library/asyncio-task.html
6. **Debounce Patterns**: https://pypi.org/project/python-debouncer/

---

**End of Specification** 🎉

Choose a proposal, and I'll create detailed implementation tasks for planloop!
