"""AI organization via GitHub Copilot CLI."""

import asyncio
from typing import AsyncIterator, Optional
from .prompts import DEFAULT_ORGANIZE_PROMPT


class AIOrganizer:
    """Manages AI organization via GitHub Copilot CLI."""

    def __init__(self, prompt_template: Optional[str] = None):
        self.prompt_template = prompt_template or DEFAULT_ORGANIZE_PROMPT

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
