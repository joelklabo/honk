"""Honk Notes - AI-assisted note-taking application."""

from .app import StreamingNotesApp
from .config import NotesConfig
from .api import NotesAPI, BufferState, EditorState
from .state import StateDetector, EditorStatus, EditorCapabilities
from .ipc import NotesIPCServer

__all__ = [
    "StreamingNotesApp",
    "NotesConfig",
    "NotesAPI",
    "BufferState",
    "EditorState",
    "StateDetector",
    "EditorStatus",
    "EditorCapabilities",
    "NotesIPCServer",
]
