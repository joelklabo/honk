# Honk Notes

AI-assisted note-taking in the terminal with GitHub Copilot integration.

## Status

✅ **Core functionality implemented and working:**
- Interactive TUI editor with auto-save
- AI organization via GitHub Copilot CLI
- Idle-based auto-organization
- Manual organization trigger (Ctrl+O)
- Agent-friendly CLI commands
- Batch processing examples
- Configuration system

⚠️ **Known limitations:**
- Widget unit tests require Textual app context (9/11 tests passing)
- Streaming animation simulated (yields full result progressively)
- File locking detection not implemented (always returns False)

## Quick Start

```bash
# Open notes editor
honk notes edit my-notes.md

# Organize with AI (non-interactive)
honk notes organize my-notes.md

# Agent-friendly commands
honk notes agent-get my-notes.md          # Read content
honk notes agent-set my-notes.md "text"   # Write content
honk notes agent-organize my-notes.md     # Organize with AI
```

## Architecture

Built on existing implementation with:
- Textual UI framework
- GitHub Copilot CLI integration
- Auto-save with debouncing
- IPC server for agent communication
- Git integration support

## Testing

```bash
# Run tests
uv run pytest tests/notes/ -v

# Current status: 9/11 passing
# Failures are widget initialization tests requiring app context
```

## Documentation

See implementation code for details:
- `src/honk/notes/app.py` - Main application
- `src/honk/notes/cli.py` - CLI commands
- `src/honk/notes/organizer.py` - AI integration
- `src/honk/notes/widgets.py` - Custom widgets
- `src/honk/notes/api.py` - Agent API

## Examples

Batch processing scripts in `examples/`:
- `batch-organize-notes.py` - Python batch script
- `organize-all-notes.sh` - Shell batch script
