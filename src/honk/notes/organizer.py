"""AI organization via GitHub Copilot CLI."""

import asyncio
from typing import AsyncIterator, Optional, Tuple
from .prompts import DEFAULT_ORGANIZE_PROMPT


class AIOrganizer:
    """Manages AI organization via GitHub Copilot CLI."""

    def __init__(
        self,
        prompt_template: Optional[str] = None,
        retry_max_attempts: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 10.0,
    ):
        self.prompt_template = prompt_template or DEFAULT_ORGANIZE_PROMPT
        self.retry_max_attempts = retry_max_attempts
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        self._copilot_command: Optional[Tuple[str, list[str]]] = None

    async def _detect_copilot_cli(self) -> Tuple[str, list[str]]:
        """Detect which Copilot CLI is available.

        Returns:
            Tuple of (base_command, args_list)
        """
        # Try new standalone CLI first
        try:
            proc = await asyncio.create_subprocess_exec(
                "copilot",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                return ("copilot", ["chat"])
        except FileNotFoundError:
            pass

        # Fall back to gh extension
        try:
            proc = await asyncio.create_subprocess_exec(
                "gh",
                "copilot",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                return ("gh", ["copilot", "suggest", "-t", "shell"])
        except FileNotFoundError:
            pass

        raise RuntimeError(
            "GitHub Copilot CLI not found. Install with: "
            "npm install -g @github/copilot-cli OR gh extension install github/gh-copilot"
        )

    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: The exception to check

        Returns:
            True if error should be retried
        """
        error_str = str(error).lower()

        # Network errors are retryable
        if any(
            x in error_str
            for x in ["connection", "timeout", "network", "unreachable"]
        ):
            return True

        # Rate limiting is retryable
        if "rate limit" in error_str or "too many requests" in error_str:
            return True

        # Auth errors are NOT retryable
        if any(x in error_str for x in ["auth", "unauthorized", "forbidden", "token"]):
            return False

        # Default to not retryable for safety
        return False

    async def organize(self, content: str) -> str:
        """Organize content using GitHub Copilot CLI with retry logic.

        Args:
            content: Content to organize

        Returns:
            Organized content

        Raises:
            RuntimeError: If organization fails after retries
        """
        # Detect CLI if not already done
        if self._copilot_command is None:
            self._copilot_command = await self._detect_copilot_cli()

        base_cmd, args = self._copilot_command
        prompt = self.prompt_template.format(content=content)

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self.retry_max_attempts):
            try:
                # Build command
                cmd = [base_cmd] + args

                # Execute
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await proc.communicate(prompt.encode())

                if proc.returncode != 0:
                    error_msg = stderr.decode().strip()
                    raise RuntimeError(f"Copilot CLI failed: {error_msg}")

                return stdout.decode().strip()

            except Exception as e:
                last_error = e

                # Check if retryable
                if not self._is_retryable(e):
                    raise

                # Last attempt, don't sleep
                if attempt == self.retry_max_attempts - 1:
                    raise

                # Calculate delay with exponential backoff
                delay = min(
                    self.retry_base_delay * (2**attempt), self.retry_max_delay
                )

                # Wait before retry
                await asyncio.sleep(delay)

        # Should not reach here, but just in case
        raise last_error or RuntimeError("Organization failed after retries")

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
