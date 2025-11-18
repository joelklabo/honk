"""Basic tests for Honk Notes functionality."""

import pytest
from honk.notes.config import NotesConfig
from honk.notes.widgets import IdleReached, StreamingTextArea
from honk.notes.organizer import AIOrganizer
from honk.notes.auto_save import AutoSaver


class TestNotesConfig:
    """Test configuration."""
    
    def test_defaults(self):
        """Test default configuration values."""
        config = NotesConfig()
        assert config.idle_timeout == 30
        assert config.auto_save is True
        assert config.auto_save_interval == 2.0
        assert config.theme == "monokai"
        assert config.language == "markdown"
    
    def test_custom_values(self):
        """Test custom configuration."""
        config = NotesConfig(
            idle_timeout=60,
            auto_save=False,
            theme="dracula"
        )
        assert config.idle_timeout == 60
        assert config.auto_save is False
        assert config.theme == "dracula"
    
    def test_load_defaults(self):
        """Test loading default config."""
        config = NotesConfig.load()
        assert isinstance(config, NotesConfig)
        assert config.idle_timeout == 30


class TestIdleReached:
    """Test IdleReached message."""
    
    def test_message_creation(self):
        """Test message carries content."""
        content = "test note content"
        msg = IdleReached(content)
        assert msg.content == content


class TestStreamingTextArea:
    """Test StreamingTextArea widget."""
    
    def test_creation(self):
        """Test widget creation."""
        editor = StreamingTextArea(idle_timeout=10)
        assert editor.idle_timeout == 10
        assert editor.last_change == 0.0
        assert editor.idle_seconds == 0
        assert editor.is_updating is False
    
    def test_default_timeout(self):
        """Test default idle timeout."""
        editor = StreamingTextArea()
        assert editor.idle_timeout == 30


class TestAIOrganizer:
    """Test AI organizer."""
    
    def test_creation(self):
        """Test organizer creation."""
        organizer = AIOrganizer()
        assert organizer.prompt_template is not None
        assert "{content}" in organizer.prompt_template
    
    def test_custom_prompt(self):
        """Test custom prompt template."""
        custom = "Organize this: {content}"
        organizer = AIOrganizer(prompt_template=custom)
        assert organizer.prompt_template == custom


class TestAutoSaver:
    """Test auto-save functionality."""
    
    def test_creation(self, tmp_path):
        """Test auto-saver creation."""
        file = tmp_path / "test.md"
        saver = AutoSaver(file, debounce_seconds=0.5)
        assert saver.file_path == file
        assert saver.debounce_seconds == 0.5
    
    def test_save_now(self, tmp_path):
        """Test immediate save."""
        file = tmp_path / "test.md"
        saver = AutoSaver(file)
        
        content = "Test content"
        saver.save_now(content)
        
        assert file.exists()
        assert file.read_text() == content
    
    @pytest.mark.asyncio
    async def test_debounced_save(self, tmp_path):
        """Test debounced save behavior."""
        import asyncio
        
        file = tmp_path / "test.md"
        saver = AutoSaver(file, debounce_seconds=0.1)
        
        # Schedule multiple saves rapidly
        await saver.schedule_save("draft 1")
        await saver.schedule_save("draft 2")
        await saver.schedule_save("draft 3")
        
        # Wait for debounce
        await asyncio.sleep(0.2)
        
        # Only last save should persist
        assert file.exists()
        assert file.read_text() == "draft 3"
