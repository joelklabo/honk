"""File watching for external changes."""

import asyncio
from pathlib import Path
from typing import Callable
from watchfiles import awatch


class FileWatcher:
    """Watches for external file changes."""

    def __init__(self, file_path: Path, callback: Callable):
        self.file_path = file_path
        self.callback = callback
        self._watch_task: asyncio.Task | None = None

    async def start(self):
        """Start watching file."""
        self._watch_task = asyncio.create_task(self._watch_loop())

    async def _watch_loop(self):
        """Main watch loop using watchfiles.awatch."""
        try:
            async for changes in awatch(self.file_path.parent):
                for change_type, changed_path in changes:
                    if Path(changed_path) == self.file_path:
                        await self.callback()
        except asyncio.CancelledError:
            pass

    def stop(self):
        """Stop watching."""
        if self._watch_task:
            self._watch_task.cancel()
