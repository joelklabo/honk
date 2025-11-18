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
        
    Returns:
        AreaMetadata describing the release area
    """
    from . import cli
    from honk.registry import AreaMetadata
    
    # Add release commands to main app
    app.add_typer(cli.app, name="release", help="Release automation tools")
    
    return AreaMetadata(
        name="release",
        description="AI-powered release automation with human oversight",
        version="0.1.0"
    )
