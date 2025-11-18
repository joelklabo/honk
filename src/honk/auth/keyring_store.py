"""Keyring storage abstraction for authentication tokens."""

import json
from pathlib import Path
from typing import Optional
import keyring

from .base import TokenMetadata


class KeyringStore:
    """Store and retrieve authentication tokens using system keyring."""
    
    SERVICE_NAME = "honk"
    METADATA_DIR = Path.home() / ".config" / "honk"
    METADATA_FILE = METADATA_DIR / "auth.json"
    
    def __init__(self):
        """Initialize keyring store."""
        self.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def store_token(self, key: str, token: str) -> None:
        """Store a token in the system keyring."""
        keyring.set_password(self.SERVICE_NAME, key, token)
    
    def retrieve_token(self, key: str) -> Optional[str]:
        """Retrieve a token from the system keyring."""
        return keyring.get_password(self.SERVICE_NAME, key)
    
    def delete_token(self, key: str) -> None:
        """Delete a token from the system keyring."""
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
        except keyring.errors.PasswordDeleteError:
            pass
    
    def store_metadata(self, key: str, metadata: TokenMetadata) -> None:
        """Store token metadata to config file."""
        all_metadata = self._load_all_metadata()
        all_metadata[key] = metadata.model_dump()
        self._save_all_metadata(all_metadata)
    
    def retrieve_metadata(self, key: str) -> Optional[TokenMetadata]:
        """Retrieve token metadata from config file."""
        all_metadata = self._load_all_metadata()
        if key in all_metadata:
            return TokenMetadata(**all_metadata[key])
        return None
    
    def _load_all_metadata(self) -> dict:
        """Load all metadata from config file."""
        if not self.METADATA_FILE.exists():
            return {}
        try:
            with open(self.METADATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_all_metadata(self, metadata: dict) -> None:
        """Save all metadata to config file."""
        with open(self.METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
