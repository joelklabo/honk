"""Debounced auto-save functionality."""

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
