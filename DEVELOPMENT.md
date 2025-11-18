# Honk Development Guide

## Installation for Development

Honk is installed as an **editable package** using `uv tool install --editable .`

### What This Means

✅ **Auto-updating**: Any changes to the source code in `/Users/honk/code/honk/src/honk/` are **immediately reflected** when you run `honk`

✅ **No reinstall needed**: Edit code, run `honk`, see changes instantly

✅ **Global availability**: `honk` command works from any directory

### Current Installation

```bash
# Installation location
~/.local/share/uv/tools/honk/

# Executable location
~/.local/bin/honk

# Source code (editable)
/Users/honk/code/honk/src/honk/
```

### Verify Installation

```bash
# Check if editable install is active
uv tool list --show-paths
# Should show: honk v0.1.0 with editable path

# View receipt
cat ~/.local/share/uv/tools/honk/uv-receipt.toml
# Should show: editable = "/Users/honk/code/honk"
```

### Development Workflow

1. **Make changes** to code in `src/honk/`
2. **Run tests**: `uv run pytest`
3. **Test immediately**: `honk <command>` (no reinstall needed!)
4. **Commit**: `git commit -m "..."`

### If You Need to Reinstall

```bash
# Uninstall
uv tool uninstall honk

# Reinstall (editable)
cd /Users/honk/code/honk
uv tool install --editable .
```

### Troubleshooting

**Problem**: Changes not reflecting

**Solutions**:
1. Check if editable install is active: `uv tool list --show-paths`
2. Verify you're editing the right path: `/Users/honk/code/honk/src/honk/`
3. Check for Python bytecode cache issues: `find . -type d -name __pycache__ -exec rm -rf {} +`
4. Reinstall: `uv tool uninstall honk && uv tool install --editable .`

**Problem**: Import errors

**Solution**: Make sure you're in the honk directory when running tests:
```bash
cd /Users/honk/code/honk
uv run pytest
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/watchdog/test_pty_scanner.py

# Run with coverage
uv run pytest --cov=honk --cov-report=html

# Lint
uv run ruff check

# Type check
uv run mypy src/honk/
```

### Adding New Features

1. Create feature branch: `git checkout -b feature/my-feature`
2. Write tests first (TDD)
3. Implement feature
4. Test with `honk` command (changes are live!)
5. Run full test suite: `uv run pytest`
6. Lint: `uv run ruff check`
7. Commit: `git commit -m "feat: my feature"`
8. Merge to main

### Current Features

- ✅ `honk watchdog pty show` - PTY monitoring
- ✅ `honk watchdog pty clean` - PTY cleanup
- ✅ `honk watchdog pty watch` - Continuous monitoring
- ✅ `honk auth gh` - GitHub authentication
- ✅ `honk auth az` - Azure DevOps authentication
- ✅ `honk doctor` - Prerequisite checks
- ✅ `honk introspect` - Command catalog

### Editable Install Benefits

🚀 **Instant feedback**: No build/install cycle  
🔧 **Easy debugging**: Change code, run immediately  
✅ **Real environment**: Test in production-like setup  
🎯 **Efficient**: No time wasted on reinstalls

---

**Note**: The editable install is already configured and working! Your changes to the source code will be immediately available when you run `honk`.

## Progress UI Components

### Overview

Honk includes reusable progress components for showing feedback during long-running operations.

### Usage

```python
from honk.ui import progress_step, progress_tracker

# Simple spinner for single operation
with progress_step("Loading data"):
    data = load()

# Multi-step progress
with progress_tracker() as tracker:
    tracker.step("Phase 1...")
    work1()
    
    tracker.step("Phase 2", total=100)
    for i in range(100):
        work2(i)
        tracker.advance()
    
    tracker.complete("Done!")
```

### Features

- **Silent in --json mode** - No output pollution for agents
- **Transient display** - Disappears after completion
- **Semantic tokens** - Uses design system colors
- **Context managers** - Automatic cleanup

### Design Principles

1. Show feedback for operations >2 seconds
2. Use spinners for indeterminate operations
3. Use progress bars when you can count steps
4. Always respect --json mode (set HONK_JSON_MODE=1)

### Examples in Codebase

See `src/honk/watchdog/pty_cli.py` for real usage:
- `show` command uses `progress_step()` during PTY scanning
- `clean` command uses progress for scanning and cleanup

### Testing

```python
def test_with_progress(monkeypatch):
    monkeypatch.setenv("HONK_JSON_MODE", "1")  # Force silent
    
    with progress_step("Testing"):
        work()
    
    # No output in JSON mode
```

See `tests/ui/test_progress.py` for comprehensive examples.

## Logging

### Overview

Honk uses a centralized, structured logging system for recording significant events. This ensures that all log entries are consistent and easily machine-readable.

### Usage

To log an event, import and use the `log_event` function from the `honk.log` module.

```python
from honk.log import log_event

# ...

log_event("my_event_type", {
    "key": "value",
    "another_key": 123
})
```

### Key Principles

- **Log significant events**: Use logging for events that have an impact, such as automated actions, errors, or important state changes. Do not log trivial operations.
- **Structured data**: The `data` payload must be a dictionary that can be serialized to JSON.
- **Centralized log file**: All events are logged to a single, rotating log file located at `~/.local/state/honk/honk.log`.

### Example in Codebase

See `src/honk/watchdog/pty_cli.py` for an example of how the `watch` command logs cleanup events.