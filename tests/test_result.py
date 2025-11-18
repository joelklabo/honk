"""Tests for result envelope."""
import pytest
from honk.result import ResultEnvelope, Link, NextStep, PackResult, EXIT_OK


def test_result_envelope_basic():
    """Test basic result envelope creation."""
    result = ResultEnvelope(
        command=["honk", "test"],
        status="ok",
        code="test.ok",
        summary="Test passed",
        run_id="test-123",
        duration_ms=100
    )
    assert result.version == "1.0"
    assert result.command == ["honk", "test"]
    assert result.status == "ok"
    assert result.changed is False
    assert result.facts == {}


def test_result_envelope_with_links():
    """Test result envelope with links."""
    result = ResultEnvelope(
        command=["honk", "test"],
        status="ok",
        code="test.ok",
        summary="Test passed",
        run_id="test-123",
        duration_ms=100,
        links=[Link(rel="docs", href="https://example.com")]
    )
    assert len(result.links) == 1
    assert result.links[0].rel == "docs"


def test_result_envelope_with_next_steps():
    """Test result envelope with next steps."""
    result = ResultEnvelope(
        command=["honk", "test"],
        status="ok",
        code="test.ok",
        summary="Test passed",
        run_id="test-123",
        duration_ms=100,
        next=[NextStep(run=["honk", "next"], summary="Run next command")]
    )
    assert len(result.next) == 1
    assert result.next[0].run == ["honk", "next"]


def test_exit_codes():
    """Test exit code constants."""
    assert EXIT_OK == 0
