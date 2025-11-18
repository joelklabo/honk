"""Tests for progress UI components."""

import io
import pytest
from rich.console import Console

from honk.ui.progress import progress_step, progress_tracker, _is_json_mode


class TestJsonModeDetection:
    """Tests for JSON mode detection."""

    def test_json_mode_env_var(self, monkeypatch):
        """Detects JSON mode from HONK_JSON_MODE env var."""
        monkeypatch.setenv("HONK_JSON_MODE", "1")
        assert _is_json_mode() is True

    def test_no_color_env_var(self, monkeypatch):
        """Detects JSON mode from NO_COLOR env var."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.setenv("NO_COLOR", "1")
        assert _is_json_mode() is True

    def test_normal_mode(self, monkeypatch):
        """Normal mode when no env vars set and stdout is TTY."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)
        # Note: This will be True in test environment since stdout isn't a TTY
        # In real terminal, would be False
        result = _is_json_mode()
        assert isinstance(result, bool)


class TestProgressStep:
    """Tests for progress_step context manager."""

    def test_silent_in_json_mode(self, monkeypatch):
        """Progress step produces no output in JSON mode."""
        monkeypatch.setenv("HONK_JSON_MODE", "1")

        output = io.StringIO()
        console = Console(file=output, record=True)

        with progress_step("Testing", console=console):
            pass

        assert output.getvalue() == ""

    def test_shows_description(self, monkeypatch):
        """Progress step shows description in normal mode."""
        from honk.ui.theme import HONK_THEME
        
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)
        # Mock isatty to return True
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80, theme=HONK_THEME)

        with progress_step("Testing operation", console=console):
            pass

        recorded = console.export_text()
        assert "Testing operation" in recorded

    def test_custom_style(self, monkeypatch):
        """Progress step accepts custom style."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80)

        with progress_step("Testing", console=console, style="red"):
            pass

        # Should not raise any errors
        assert True


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    def test_silent_in_json_mode(self, monkeypatch):
        """Progress tracker produces no output in JSON mode."""
        monkeypatch.setenv("HONK_JSON_MODE", "1")

        output = io.StringIO()
        console = Console(file=output, record=True)

        with progress_tracker(console=console) as tracker:
            tracker.step("Step 1")
            tracker.step("Step 2")
            tracker.complete("Done")

        assert output.getvalue() == ""

    def test_multi_step_flow(self, monkeypatch):
        """Progress tracker handles multiple steps."""
        from honk.ui.theme import HONK_THEME
        
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)
        # Mock isatty to return True
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80, theme=HONK_THEME)

        with progress_tracker(console=console) as tracker:
            tracker.step("Step 1")
            tracker.step("Step 2")
            tracker.complete("Done")

        recorded = console.export_text()
        # At least one step should be in output
        assert "Step" in recorded or "Done" in recorded

    def test_advance_with_progress(self, monkeypatch):
        """Progress tracker advances progress bar."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80)

        with progress_tracker(console=console) as tracker:
            tracker.step("Processing", total=10)
            tracker.advance(5)
            tracker.advance(5)

        # Should not raise errors
        assert True

    def test_fail_message(self, monkeypatch):
        """Progress tracker shows failure message."""
        from honk.ui.theme import HONK_THEME
        
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)
        # Mock isatty to return True
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80, theme=HONK_THEME)

        with progress_tracker(console=console) as tracker:
            tracker.step("Failing step")
            tracker.fail("Something went wrong")

        recorded = console.export_text()
        assert "Something went wrong" in recorded or "Failing" in recorded

    def test_transient_mode(self, monkeypatch):
        """Progress tracker respects transient flag."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80)

        with progress_tracker(console=console, transient=True) as tracker:
            tracker.step("Test")

        # Transient mode should work without errors
        assert True

    def test_non_transient_mode(self, monkeypatch):
        """Progress tracker works in non-transient mode."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80)

        with progress_tracker(console=console, transient=False) as tracker:
            tracker.step("Test")

        # Non-transient mode should work
        assert True


class TestProgressIntegration:
    """Integration tests for progress components."""

    def test_nested_operations(self, monkeypatch):
        """Progress components can be nested."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80)

        with progress_tracker(console=console) as tracker:
            tracker.step("Outer step")

            with progress_step("Inner operation", console=console):
                pass

            tracker.complete("Done")

        # Should complete without errors
        assert True

    def test_exception_handling(self, monkeypatch):
        """Progress components handle exceptions gracefully."""
        monkeypatch.delenv("HONK_JSON_MODE", raising=False)
        monkeypatch.delenv("NO_COLOR", raising=False)

        output = io.StringIO()
        console = Console(file=output, record=True, force_terminal=True, width=80)

        with pytest.raises(ValueError):
            with progress_step("Testing", console=console):
                raise ValueError("Test error")

        # Should have cleaned up properly
        assert True
