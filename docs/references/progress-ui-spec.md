# Honk Progress UI Component - Implementation Specification

**Version:** 1.0  
**Status:** Draft  
**Created:** 2025-11-18  
**Component:** `ui.progress`

---

## Executive Summary

This spec defines a reusable progress UI component system for Honk CLI tools. The component provides visual feedback during long-running operations while respecting Honk's "agent-first" design principle (silent in `--json` mode, informative for humans).

**Problem:** Operations like `honk watchdog pty show` take 2-3 seconds with no feedback, creating poor UX.

**Solution:** Rich-based progress tracking with semantic token integration, multi-step support, and automatic JSON-mode silence.

---

## Design Principles

1. **Agent-First**: Silent in `--json` mode (no output pollution)
2. **Transient**: Progress UI disappears after completion
3. **Semantic**: Uses design system tokens for consistency
4. **Simple API**: Context managers for ease of use
5. **Composable**: Works with existing Rich/Typer patterns
6. **Testable**: Mockable and verifiable

---

## Component Architecture

### Module Structure

```
src/honk/ui/
├── __init__.py              # Exports console, print helpers, progress
├── theme.py                 # Existing theme/tokens
├── progress.py              # NEW: Progress components
└── __pycache__/
```

### API Overview

```python
from honk.ui import progress_step, progress_tracker

# Simple spinner for single operation
with progress_step("Scanning PTYs"):
    results = scan_ptys()

# Multi-step tracker with substeps
with progress_tracker() as tracker:
    tracker.step("Running lsof...")
    output = run_lsof()
    
    tracker.step("Parsing processes...")
    processes = parse(output)
    
    tracker.step("Analyzing leaks...")
    leaks = find_leaks(processes)
    
    tracker.complete("Found 128 PTYs")
```

---

## Implementation Specification

### 1. `progress_step()` - Simple Spinner

**Purpose:** Show spinner for single indeterminate operation.

**Signature:**
```python
@contextmanager
def progress_step(
    description: str,
    *,
    console: Console | None = None,
    spinner: str = "dots",
    style: str = "emphasis",
) -> Iterator[None]:
    """Display transient spinner during operation.
    
    Args:
        description: Operation description (e.g., "Scanning PTYs")
        console: Rich Console (default: ui.console)
        spinner: Spinner type (default: "dots")
        style: Semantic token from theme (default: "emphasis")
    
    Yields:
        None
    
    Example:
        with progress_step("Loading data"):
            data = load()
    """
```

**Behavior:**
- Auto-detects `--json` mode (checks `os.getenv("HONK_JSON_MODE")`)
- If JSON mode: Silent (no-op)
- If terminal: Shows spinner with description
- On exit: Clears spinner (transient)
- On exception: Shows error state before re-raising

**Visual Output:**
```
⠋ Scanning PTYs...
```

### 2. `progress_tracker()` - Multi-Step Progress

**Purpose:** Track progress through multiple steps with optional substep counting.

**Signature:**
```python
@contextmanager
def progress_tracker(
    *,
    console: Console | None = None,
    transient: bool = True,
) -> Iterator[ProgressTracker]:
    """Create multi-step progress tracker.
    
    Args:
        console: Rich Console (default: ui.console)
        transient: Clear on completion (default: True)
    
    Yields:
        ProgressTracker instance
    
    Example:
        with progress_tracker() as tracker:
            tracker.step("Phase 1")
            work()
            tracker.step("Phase 2", total=100)
            for i in range(100):
                tracker.advance()
    """
```

**ProgressTracker API:**
```python
class ProgressTracker:
    def step(
        self,
        description: str,
        *,
        total: int | None = None,
        style: str = "emphasis",
    ) -> None:
        """Start new step (completes previous).
        
        Args:
            description: Step description
            total: Total units (None = spinner, int = progress bar)
            style: Semantic token
        """
    
    def advance(self, n: int = 1) -> None:
        """Advance current step progress by n units."""
    
    def complete(self, summary: str | None = None) -> None:
        """Complete tracking with optional summary message."""
    
    def fail(self, error: str) -> None:
        """Mark current step as failed."""
```

**Visual Output:**
```
⠋ Running lsof...
⠋ Parsing 1,129 processes...
⠋ Analyzing leaks...
✓ Found 128 PTYs across 1,129 processes
```

With progress bar:
```
Running lsof... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01
Parsing processes... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 75% 0:00:02
```

### 3. Silent Mode Detection

**Mechanism:**
```python
def _is_json_mode() -> bool:
    """Check if running in JSON output mode."""
    return (
        os.getenv("HONK_JSON_MODE") == "1" or
        os.getenv("NO_COLOR") is not None or
        not sys.stdout.isatty()
    )
```

**CLI Integration:**
Commands set environment variable:
```python
@app.command()
def show(json_output: bool = typer.Option(False, "--json")):
    if json_output:
        os.environ["HONK_JSON_MODE"] = "1"
    
    with progress_step("Scanning PTYs"):
        results = scan_ptys()  # No spinner shown in JSON mode
```

### 4. Design System Integration

**Semantic Tokens Used:**
- `emphasis` - Current operation (cyan)
- `success` - Completion message (green)
- `error` - Failure message (red)
- `dim` - Substep details (gray)

**Example Usage:**
```python
tracker.step("Scanning", style="emphasis")
tracker.complete("Done!", style="success")
tracker.fail("Connection timeout", style="error")
```

---

## Usage Examples

### Example 1: Simple Operation

**Before:**
```python
def show():
    processes = scan_ptys()  # 2s pause, no feedback
    print_results(processes)
```

**After:**
```python
def show():
    with progress_step("Scanning PTYs"):
        processes = scan_ptys()
    print_results(processes)
```

### Example 2: Multi-Step with Progress

```python
def clean():
    with progress_tracker() as tracker:
        tracker.step("Scanning PTYs...")
        processes_before = scan_ptys()
        
        tracker.step("Identifying leaks...")
        leaks = get_suspected_leaks(processes_before)
        
        if not leaks:
            tracker.complete("No leaks found")
            return
        
        tracker.step(f"Killing {len(leaks)} processes...", total=len(leaks))
        for pid in leaks:
            kill_process(pid)
            tracker.advance()
        
        tracker.step("Verifying cleanup...")
        processes_after = scan_ptys()
        
        freed = len(processes_before) - len(processes_after)
        tracker.complete(f"Freed {freed} PTYs")
```

### Example 3: Error Handling

```python
def validate():
    with progress_tracker() as tracker:
        try:
            tracker.step("Checking prerequisites...")
            check_lsof()
            
            tracker.step("Running diagnostics...")
            results = run_diagnostics()
            
            tracker.complete("All checks passed")
        except RuntimeError as e:
            tracker.fail(str(e))
            raise
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/ui/test_progress.py`

```python
def test_progress_step_silent_mode():
    """Progress step is silent in JSON mode."""
    os.environ["HONK_JSON_MODE"] = "1"
    
    output = io.StringIO()
    console = Console(file=output, record=True)
    
    with progress_step("Testing", console=console):
        pass
    
    assert output.getvalue() == ""

def test_progress_step_shows_spinner():
    """Progress step shows spinner in terminal mode."""
    output = io.StringIO()
    console = Console(file=output, record=True, force_terminal=True)
    
    with progress_step("Testing", console=console):
        pass
    
    recorded = console.export_text()
    assert "Testing" in recorded

def test_progress_tracker_advances():
    """Progress tracker advances through steps."""
    output = io.StringIO()
    console = Console(file=output, record=True, force_terminal=True)
    
    with progress_tracker(console=console) as tracker:
        tracker.step("Step 1")
        tracker.step("Step 2", total=10)
        tracker.advance(5)
        tracker.complete("Done")
    
    recorded = console.export_text()
    assert "Step 1" in recorded
    assert "Step 2" in recorded
    assert "Done" in recorded
```

### Integration Tests

**File:** `tests/watchdog/test_pty_cli_progress.py`

```python
def test_show_command_with_progress():
    """Show command displays progress feedback."""
    result = subprocess.run(
        ["honk", "watchdog", "pty", "show"],
        capture_output=True,
        text=True,
        env={**os.environ, "FORCE_COLOR": "1"}
    )
    
    # Should have shown progress (transient, so not in final output)
    assert result.returncode == 0
    assert "PTY Usage" in result.stdout

def test_show_command_json_no_progress():
    """JSON mode produces no progress output."""
    result = subprocess.run(
        ["honk", "watchdog", "pty", "show", "--json"],
        capture_output=True,
        text=True
    )
    
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    # No stderr output (progress would be there)
    assert result.stderr == ""
```

---

## Implementation Phases

### Phase 1: Core Component (2 hours)
- [ ] Create `src/honk/ui/progress.py`
- [ ] Implement `progress_step()`
- [ ] Implement `progress_tracker()` and `ProgressTracker` class
- [ ] Add silent mode detection
- [ ] Export from `src/honk/ui/__init__.py`
- [ ] Write unit tests (90%+ coverage)

### Phase 2: Apply to watchdog pty (1 hour)
- [ ] Update `scan_ptys()` to accept progress callback
- [ ] Add progress to `show` command
- [ ] Add progress to `clean` command  
- [ ] Add progress to `watch` command (optional)
- [ ] Verify no output in `--json` mode
- [ ] Write integration tests

### Phase 3: Documentation (30 min)
- [ ] Update design system docs
- [ ] Add to `DEVELOPMENT.md`
- [ ] Create example in demo commands
- [ ] Add to CLI design system reference

### Phase 4: Rollout (30 min)
- [ ] Update other tools (auth, doctor) with progress
- [ ] Add to command template/generator
- [ ] Update spec.md with progress patterns
- [ ] Commit and merge

**Total Estimated Time:** 4 hours

---

## Acceptance Criteria

### Functionality
- [ ] `progress_step()` shows spinner for operations
- [ ] `progress_tracker()` handles multi-step operations
- [ ] Progress UI is transient (disappears on completion)
- [ ] Silent in `--json` mode (no output pollution)
- [ ] Uses semantic tokens from design system
- [ ] Error states display correctly
- [ ] Context managers clean up properly

### Testing
- [ ] Unit tests achieve >90% coverage
- [ ] Integration tests verify end-to-end behavior
- [ ] Tests verify silent mode works
- [ ] Tests don't slow down (no real timing dependencies)
- [ ] Error paths are tested

### Documentation
- [ ] API documented with examples
- [ ] Design system updated
- [ ] DEVELOPMENT.md includes progress patterns
- [ ] Demo command shows usage

### Integration
- [ ] watchdog pty commands use progress
- [ ] No regressions in existing commands
- [ ] All tests pass (including new ones)
- [ ] Linting and type checking clean

---

## Future Enhancements

### Phase 5 (Optional)
1. **Duration Display** - Show elapsed time for long operations
2. **ETA Calculation** - Estimate time remaining (for determinate progress)
3. **Speed Metrics** - Show items/second for batch operations
4. **Nested Progress** - Hierarchical progress trees
5. **Custom Spinners** - Per-operation spinner styles
6. **Progress Persistence** - Optional non-transient mode for debugging
7. **Live Log Streaming** - Show operation logs while progressing

---

## Dependencies

**Existing:**
- `rich` (already in project) - Progress/Status/Console
- `typer` (already in project) - CLI framework

**New:** None

---

## Security & Performance

**Security:**
- No sensitive data in progress messages
- No command injection (all strings are user-controlled or validated)

**Performance:**
- Minimal overhead (<10ms per operation)
- Transient display reduces terminal buffer usage
- Silent mode has zero overhead (early return)

---

## Rollback Plan

If issues arise:
1. Progress component is opt-in via `with` statements
2. Remove `with progress_step()` wrappers to revert
3. Component is isolated in `ui/progress.py` (easy to disable)
4. No breaking changes to existing APIs

---

## References

- [Rich Progress Documentation](https://rich.readthedocs.io/en/stable/progress.html)
- [Typer Progress Bar Guide](https://typer.tiangolo.com/tutorial/progressbar/)
- [CLI UX Best Practices](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays)
- [Honk Design System](../design-system.md)
- [Honk Spec](../spec.md)

---

**Spec Status:** ✅ Ready for implementation

**Next Step:** Add to planloop and begin Phase 1
