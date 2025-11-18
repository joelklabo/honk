"""Honk CLI design system - colors, styles, and output helpers."""

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

# Create shared console instance
console = Console(theme=HONK_THEME)


# Status message helpers with icons
def print_success(msg: str) -> None:
    """Print success message with checkmark."""
    console.print(f"✓ {msg}", style="success")


def print_error(msg: str) -> None:
    """Print error message with X."""
    console.print(f"✗ {msg}", style="error")


def print_warning(msg: str) -> None:
    """Print warning message with warning symbol."""
    console.print(f"⚠ {msg}", style="warning")


def print_info(msg: str) -> None:
    """Print info message with info symbol."""
    console.print(f"ℹ {msg}", style="info")


def print_dim(msg: str) -> None:
    """Print dimmed secondary information."""
    console.print(msg, style="dim")


# Structured output helpers
def print_kv(key: str, value: str) -> None:
    """Print key-value pair with styled key."""
    console.print(f"[key]{key}:[/key] [value]{value}[/value]")


def print_code(code: str) -> None:
    """Print code snippet."""
    console.print(code, style="code")
