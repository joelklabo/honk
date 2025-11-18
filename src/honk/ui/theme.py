"""Honk CLI design system - colors, styles, and output helpers."""

import os
from rich.console import Console
from rich.theme import Theme

# Define semantic color tokens
HONK_THEME = Theme({
    # Status messages
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "dim cyan",
    
    # UI elements
    "dim": "dim white",
    "emphasis": "bold",
    "code": "dim white",
    "key": "cyan",
    "value": "white",
    
    # Branding (optional)
    "brand": "magenta",
})

# Create shared console instance with NO_COLOR support
_no_color = os.getenv("NO_COLOR") or os.getenv("HONK_NO_COLOR")
console = Console(theme=HONK_THEME, no_color=bool(_no_color), force_terminal=True)


# Status message helpers with icons
def print_success(msg: str) -> None:
    """Print success message with checkmark."""
    _get_console().print(f"✓ {msg}", style="success")


def print_error(msg: str) -> None:
    """Print error message with X."""
    _get_console().print(f"✗ {msg}", style="error")


def print_warning(msg: str) -> None:
    """Print warning message with warning symbol."""
    _get_console().print(f"⚠ {msg}", style="warning")


def print_info(msg: str) -> None:
    """Print info message with info symbol."""
    _get_console().print(f"ℹ {msg}", style="info")


def print_dim(msg: str) -> None:
    """Print dimmed secondary information."""
    _get_console().print(msg, style="dim")


def _get_console() -> Console:
    """Get console instance respecting current NO_COLOR setting."""
    no_color = bool(os.getenv("NO_COLOR") or os.getenv("HONK_NO_COLOR"))
    return Console(theme=HONK_THEME, no_color=no_color, force_terminal=True)


# Structured output helpers
def print_kv(key: str, value: str) -> None:
    """Print key-value pair with styled key."""
    _get_console().print(f"[key]{key}:[/key] [value]{value}[/value]")


def print_code(code: str) -> None:
    """Print code snippet."""
    _get_console().print(code, style="code")
