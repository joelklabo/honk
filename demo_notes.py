#!/usr/bin/env python3
"""Demo script for Honk Notes - shows features without requiring full setup."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from honk.ui import console, print_success, print_info

def show_header():
    """Show demo header."""
    header = Text()
    header.append("🤖 Honk Notes - AI-Assisted Note-Taking\n", style="bold cyan")
    header.append("Terminal-based notes with automatic AI organization", style="dim")
    
    console.print(Panel(header, border_style="cyan"))
    console.print()


def show_features():
    """Show key features."""
    print_info("Key Features:")
    console.print()
    
    features = [
        ("🎨", "Beautiful TUI", "Polished interface using Honk's design system"),
        ("🤖", "AI Organization", "Automatic reorganization via GitHub Copilot"),
        ("⚡", "Real-time Editing", "Smooth, flicker-free markdown editing"),
        ("💾", "Auto-save", "Never lose work (debounced)"),
        ("⏱️", "Smart Idle Detection", "AI kicks in after 30s idle"),
        ("⌨️", "Keyboard Shortcuts", "Efficient workflows"),
    ]
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan", width=3)
    table.add_column(style="bold", width=20)
    table.add_column(style="dim")
    
    for icon, title, desc in features:
        table.add_row(icon, title, desc)
    
    console.print(table)
    console.print()


def show_example():
    """Show before/after example."""
    print_info("Example: Before & After AI Organization")
    console.print()
    
    before = """
**Your Raw Notes:**

- discussed API redesign
- bob suggested GraphQL
- alice prefers REST  
- need to decide by Friday
- important: backwards compatibility
- performance concerns
- testing required
"""

    after = """
**After AI Organization:**

## Meeting Summary

### API Redesign Discussion

**Options Discussed:**
- GraphQL (suggested by Bob)
- REST (preferred by Alice)

### Key Considerations
- Performance implications
- Testing requirements

### Action Items
- [ ] Make architecture decision by Friday

> Important: Ensure backwards compatibility
"""
    
    console.print(Panel(before.strip(), title="[bold]Before[/bold]", border_style="yellow"))
    console.print()
    console.print(Panel(after.strip(), title="[bold]After[/bold]", border_style="green"))
    console.print()


def show_commands():
    """Show available commands."""
    print_info("Quick Start Commands:")
    console.print()
    
    commands = Table(show_header=True, box=None, padding=(0, 2))
    commands.add_column("Command", style="cyan", no_wrap=True)
    commands.add_column("Description", style="white")
    
    commands.add_row(
        "honk notes edit meeting.md",
        "Open editor for meeting.md"
    )
    commands.add_row(
        "honk notes edit --idle 60 notes.md",
        "Custom idle timeout (60s)"
    )
    commands.add_row(
        "honk notes organize draft.md",
        "Organize file (non-interactive)"
    )
    commands.add_row(
        "honk notes organize notes.md --dry-run",
        "Preview organization"
    )
    
    console.print(commands)
    console.print()


def show_shortcuts():
    """Show keyboard shortcuts."""
    print_info("Keyboard Shortcuts:")
    console.print()
    
    shortcuts = Table(show_header=False, box=None, padding=(0, 2))
    shortcuts.add_column(style="cyan bold", width=10)
    shortcuts.add_column(style="white")
    
    shortcuts.add_row("Ctrl+O", "Organize notes now")
    shortcuts.add_row("Ctrl+S", "Save file")
    shortcuts.add_row("Ctrl+Z", "Undo changes")
    shortcuts.add_row("Ctrl+Q", "Quit editor")
    
    console.print(shortcuts)
    console.print()


def show_design_system():
    """Show design system integration."""
    print_info("Honk Design System Integration:")
    console.print()
    
    console.print("  Colors & Styling:", style="bold")
    console.print("    • Brand: ", end="")
    console.print("Cyan accents", style="cyan bold")
    console.print("    • Success: ", end="")
    console.print("✓ Operations completed", style="success")
    console.print("    • Error: ", end="")
    console.print("✗ Failed operations", style="error")
    console.print("    • Warning: ", end="")
    console.print("⚠ Important notices", style="warning")
    console.print("    • Info: ", end="")
    console.print("ℹ Helpful information", style="info")
    console.print()
    
    console.print("  Components:", style="bold")
    console.print("    • Progress indicators with spinners")
    console.print("    • Semantic color tokens")
    console.print("    • Consistent typography")
    console.print("    • Smooth animations")
    console.print()


def show_next_steps():
    """Show next steps."""
    console.print()
    print_success("Ready to try it!")
    console.print()
    
    console.print("Next steps:", style="bold")
    console.print("  1. Run validation tests:")
    console.print("     [cyan]python3 test_notes_setup.py[/cyan]", style="dim")
    console.print()
    console.print("  2. Try the editor:")
    console.print("     [cyan]honk notes edit test.md[/cyan]", style="dim")
    console.print()
    console.print("  3. Read the user guide:")
    console.print("     [cyan]docs/notes-user-guide.md[/cyan]", style="dim")
    console.print()


def main():
    """Run demo."""
    show_header()
    show_features()
    show_example()
    show_commands()
    show_shortcuts()
    show_design_system()
    show_next_steps()
    
    console.print()
    console.print("─" * 60, style="dim")
    console.print()
    console.print("🎉 Honk Notes combines terminal simplicity with AI power!", style="bold green")
    console.print("   Focus on ideas. Let AI handle structure.", style="dim")
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\nDemo interrupted.", style="dim")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[error]Demo error: {e}[/error]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
