"""Demo command showing progress UI usage."""

import time
import typer
from ..ui import progress_step, progress_tracker

demo_progress_app = typer.Typer(help="Progress UI demonstrations")


@demo_progress_app.command("simple")
def simple_spinner():
    """Simple spinner demo."""
    with progress_step("Loading data"):
        time.sleep(2)
    print("✓ Done!")


@demo_progress_app.command("multi")
def multi_step():
    """Multi-step progress demo."""
    with progress_tracker() as tracker:
        tracker.step("Initializing...")
        time.sleep(1)
        
        tracker.step("Processing items", total=20)
        for i in range(20):
            time.sleep(0.1)
            tracker.advance()
        
        tracker.step("Finalizing...")
        time.sleep(0.5)
        
        tracker.complete("Processed 20 items successfully!")


@demo_progress_app.command("error")
def error_demo():
    """Progress with error handling."""
    with progress_tracker() as tracker:
        tracker.step("Step 1...")
        time.sleep(1)
        
        tracker.step("Step 2 (will fail)...")
        try:
            raise ValueError("Simulated error")
        except ValueError as e:
            tracker.fail(str(e))
            raise
