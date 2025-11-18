"""Progress UI components for Honk CLI tools.

Provides reusable progress indicators (spinners, progress bars) that:
- Show feedback during long-running operations
- Silent in --json mode (agent-first design)
- Use semantic tokens from design system
- Transient (disappear after completion)
"""

import os
import sys
from contextlib import contextmanager
from typing import Iterator

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

from .theme import HONK_THEME


def _is_json_mode() -> bool:
    """Check if running in JSON output mode (should be silent)."""
    return (
        os.getenv("HONK_JSON_MODE") == "1"
        or os.getenv("NO_COLOR") is not None
        or not sys.stdout.isatty()
    )


@contextmanager
def progress_step(
    description: str,
    *,
    console: Console | None = None,
    spinner: str = "dots",
    style: str | None = None,
) -> Iterator[None]:
    """Display transient spinner during single operation.

    Args:
        description: Operation description (e.g., "Scanning PTYs")
        console: Rich Console (default: uses ui.console)
        spinner: Spinner type (default: "dots")
        style: Style/color for text (default: uses theme's emphasis)

    Yields:
        None

    Example:
        >>> with progress_step("Loading data"):
        ...     data = load()
        ⠋ Loading data...
    """
    if _is_json_mode():
        yield
        return

    if console is None:
        from . import console as default_console

        console = default_console

    # Use theme's emphasis color if no style specified
    if style is None:
        style = "emphasis"  # Use semantic token from theme

    with console.status(f"[{style}]{description}...[/{style}]", spinner=spinner):
        yield


class ProgressTracker:
    """Multi-step progress tracker with optional progress bars."""

    def __init__(self, console: Console | None = None, transient: bool = True):
        """Initialize progress tracker.

        Args:
            console: Rich Console (default: uses ui.console)
            transient: Clear display after completion (default: True)
        """
        self.transient = transient
        self.current_task_id = None
        self._silent = _is_json_mode()

        if self._silent:
            self.console = None
            self.progress = None
            return

        if console is None:
            from . import console as default_console

            console = default_console

        self.console = console

        # Create Progress with custom columns
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=transient,
        )

    def __enter__(self):
        """Enter context manager."""
        if not self._silent and self.progress:
            self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if not self._silent and self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)

    def step(
        self,
        description: str,
        *,
        total: int | None = None,
        style: str | None = None,
    ) -> None:
        """Start new step (completes previous step).

        Args:
            description: Step description
            total: Total units (None = spinner, int = progress bar)
            style: Semantic token or color (default: emphasis)
        """
        if self._silent:
            return

        # Use theme's emphasis color if no style specified
        if style is None:
            style = "emphasis"  # Use semantic token from theme

        # Apply style to description
        styled_desc = f"[{style}]{description}[/{style}]"

        # Add new task
        self.current_task_id = self.progress.add_task(styled_desc, total=total)

    def advance(self, n: int = 1) -> None:
        """Advance current step progress by n units.

        Args:
            n: Number of units to advance (default: 1)
        """
        if self._silent or self.current_task_id is None:
            return

        self.progress.update(self.current_task_id, advance=n)

    def complete(self, summary: str | None = None) -> None:
        """Complete tracking with optional summary message.

        Args:
            summary: Final summary message (default: None)
        """
        if self._silent:
            return

        if summary and self.console:
            self.console.print(f"✓ {summary}", style="success")

    def fail(self, error: str) -> None:
        """Mark current step as failed.

        Args:
            error: Error message
        """
        if self._silent:
            return

        if self.console:
            self.console.print(f"✗ {error}", style="error")


@contextmanager
def progress_tracker(
    *,
    console: Console | None = None,
    transient: bool = True,
) -> Iterator[ProgressTracker]:
    """Create multi-step progress tracker.

    Args:
        console: Rich Console (default: uses ui.console)
        transient: Clear display after completion (default: True)

    Yields:
        ProgressTracker instance

    Example:
        >>> with progress_tracker() as tracker:
        ...     tracker.step("Phase 1")
        ...     work()
        ...     tracker.step("Phase 2", total=100)
        ...     for i in range(100):
        ...         tracker.advance()
        ...     tracker.complete("Done!")
        ⠋ Phase 1
        ⠋ Phase 2 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
        ✓ Done!
    """
    tracker = ProgressTracker(console=console, transient=transient)
    with tracker:
        yield tracker
