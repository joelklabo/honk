"""Tests for retry logic in organizer."""


import pytest

from honk.notes.organizer import AIOrganizer


@pytest.mark.asyncio
async def test_is_retryable_network_errors():
    """Test network errors are marked as retryable."""
    organizer = AIOrganizer()

    assert organizer._is_retryable(RuntimeError("connection timeout"))
    assert organizer._is_retryable(RuntimeError("network unreachable"))
    assert organizer._is_retryable(RuntimeError("Connection refused"))


@pytest.mark.asyncio
async def test_is_retryable_auth_errors():
    """Test auth errors are NOT retryable."""
    organizer = AIOrganizer()

    assert not organizer._is_retryable(RuntimeError("unauthorized"))
    assert not organizer._is_retryable(RuntimeError("authentication failed"))
    assert not organizer._is_retryable(RuntimeError("forbidden access"))


@pytest.mark.asyncio
async def test_is_retryable_rate_limit():
    """Test rate limit errors are retryable."""
    organizer = AIOrganizer()

    assert organizer._is_retryable(RuntimeError("rate limit exceeded"))
    assert organizer._is_retryable(RuntimeError("too many requests"))


@pytest.mark.asyncio
async def test_retry_configuration():
    """Test retry configuration is stored."""
    organizer = AIOrganizer(
        retry_max_attempts=5, retry_base_delay=2.0, retry_max_delay=20.0
    )

    assert organizer.retry_max_attempts == 5
    assert organizer.retry_base_delay == 2.0
    assert organizer.retry_max_delay == 20.0


@pytest.mark.asyncio
async def test_detect_copilot_cli():
    """Test Copilot CLI detection."""
    organizer = AIOrganizer()

    # This will either find copilot or gh extension or raise
    try:
        base_cmd, args = await organizer._detect_copilot_cli()
        assert base_cmd in ["copilot", "gh"]
        assert isinstance(args, list)
    except RuntimeError as e:
        # Expected if neither CLI is installed
        assert "not found" in str(e).lower()
