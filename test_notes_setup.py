#!/usr/bin/env python3
"""Test script to validate Honk Notes setup and integration."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from honk.notes import StreamingNotesApp, NotesConfig
        print("  ✓ honk.notes main imports")
    except ImportError as e:
        print(f"  ✗ Failed to import honk.notes: {e}")
        return False
    
    try:
        from honk.notes.widgets import StreamingTextArea, ProcessingOverlay
        print("  ✓ honk.notes.widgets")
    except ImportError as e:
        print(f"  ✗ Failed to import widgets: {e}")
        return False
    
    try:
        from honk.notes.organizer import AIOrganizer
        print("  ✓ honk.notes.organizer")
    except ImportError as e:
        print(f"  ✗ Failed to import organizer: {e}")
        return False
    
    try:
        from honk.notes.auto_save import AutoSaver
        print("  ✓ honk.notes.auto_save")
    except ImportError as e:
        print(f"  ✗ Failed to import auto_save: {e}")
        return False
    
    try:
        from honk.notes.cli import notes_app
        print("  ✓ honk.notes.cli")
    except ImportError as e:
        print(f"  ✗ Failed to import CLI: {e}")
        return False
    
    return True


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    
    from honk.notes.config import NotesConfig
    
    # Test defaults
    config = NotesConfig()
    assert config.idle_timeout == 30, "Default idle timeout should be 30"
    assert config.auto_save == True, "Auto-save should be enabled by default"
    assert config.theme == "monokai", "Default theme should be monokai"
    print("  ✓ Config defaults correct")
    
    # Test with custom values
    config = NotesConfig(
        idle_timeout=60,
        auto_save=False,
        theme="dracula"
    )
    assert config.idle_timeout == 60
    assert config.auto_save == False
    assert config.theme == "dracula"
    print("  ✓ Config customization works")
    
    return True


def test_app_creation():
    """Test app can be created."""
    print("\nTesting app creation...")
    
    from honk.notes.app import StreamingNotesApp
    from honk.notes.config import NotesConfig
    from pathlib import Path
    
    # Create app with test config
    config = NotesConfig(file_path=Path("/tmp/test_notes.md"))
    app = StreamingNotesApp(config)
    
    assert app.config == config, "App should store config"
    assert app.organizer is not None, "App should have organizer"
    assert app.organizing == False, "App should not be organizing initially"
    
    print("  ✓ App created successfully")
    print(f"    - Config: {app.config}")
    print(f"    - Organizer: {app.organizer}")
    print(f"    - Auto-saver: {app.auto_saver}")
    
    return True


def test_cli_integration():
    """Test CLI integration."""
    print("\nTesting CLI integration...")
    
    try:
        from honk.cli import app
        print("  ✓ Main CLI app imports")
        
        # Check if notes command is registered
        commands = [cmd.name for cmd in app.registered_commands]
        groups = [grp.name for grp in app.registered_groups]
        
        print(f"    - Registered commands: {commands}")
        print(f"    - Registered groups: {groups}")
        
        if "notes" in groups:
            print("  ✓ Notes app registered in main CLI")
        else:
            print("  ✗ Notes app NOT found in CLI groups")
            print(f"    Available groups: {groups}")
            return False
            
    except Exception as e:
        print(f"  ✗ CLI integration error: {e}")
        return False
    
    return True


def test_widgets():
    """Test widgets."""
    print("\nTesting widgets...")
    
    from honk.notes.widgets import StreamingTextArea, ProcessingOverlay, IdleReached
    
    # Test IdleReached message
    msg = IdleReached("test content")
    assert msg.content == "test content"
    print("  ✓ IdleReached message works")
    
    # Test StreamingTextArea creation
    editor = StreamingTextArea(idle_timeout=10)
    assert editor.idle_timeout == 10
    assert editor.last_change == 0.0
    assert editor.idle_seconds == 0
    assert editor.is_updating == False
    print("  ✓ StreamingTextArea creates correctly")
    
    # Test ProcessingOverlay creation
    overlay = ProcessingOverlay()
    print("  ✓ ProcessingOverlay creates correctly")
    
    return True


def test_file_structure():
    """Test that all expected files exist."""
    print("\nTesting file structure...")
    
    base = Path(__file__).parent / "src" / "honk" / "notes"
    
    expected_files = [
        "__init__.py",
        "app.py",
        "auto_save.py",
        "cli.py",
        "config.py",
        "organizer.py",
        "prompts.py",
        "widgets.py",
    ]
    
    for filename in expected_files:
        filepath = base / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} NOT FOUND")
            return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Honk Notes - Setup Validation")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Widgets", test_widgets),
        ("App Creation", test_app_creation),
        ("CLI Integration", test_cli_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Honk Notes is ready to use.")
        print("\nNext steps:")
        print("  1. Try: honk notes edit test.md")
        print("  2. Try: honk notes organize tests/notes/fixtures/sample_notes.md --dry-run")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
