#!/usr/bin/env python3
"""
Example: Batch organize all notes in a directory.

Usage:
    python examples/batch-organize-notes.py ~/notes/
"""

import sys
from pathlib import Path
import subprocess


def organize_all_notes(notes_dir: Path):
    """Organize all markdown files in directory."""
    if not notes_dir.exists():
        print(f"Error: Directory not found: {notes_dir}")
        sys.exit(1)

    notes = list(notes_dir.glob("*.md"))
    if not notes:
        print(f"No markdown files found in {notes_dir}")
        return

    print(f"Found {len(notes)} note files")

    for note_file in notes:
        print(f"Processing {note_file.name}...", end=" ")

        try:
            result = subprocess.run(
                ["honk", "notes", "agent-organize", str(note_file)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("✓ Done")
            else:
                print(f"✗ Failed: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            print("✗ Timeout")
        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: batch-organize-notes.py <directory>")
        sys.exit(1)

    notes_dir = Path(sys.argv[1])
    organize_all_notes(notes_dir)
