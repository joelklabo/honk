"""
Honk Release Tool - AI-powered release automation.

This module provides intelligent release automation with human oversight.
Supports version bumping, changelog generation, PyPI publishing, and more.
"""

__all__ = ["register"]


def register(app):
    """Register the release tool with the main CLI.
    
    Args:
        app: The main Typer application
    """
    from . import cli
    
    # Add release commands to main app
    app.add_typer(cli.app, name="release", help="Release automation tools")
