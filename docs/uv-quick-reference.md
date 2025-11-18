# UV Quick Reference for Honk Development

**Rule #1: Always use `uv run` for Python operations**

## Common Commands

### Testing
```bash
uv run pytest                              # All tests
uv run pytest tests/notes/ -v             # Specific directory, verbose
uv run pytest -k test_config              # Tests matching pattern
uv run pytest --cov=src/honk              # With coverage
uv run pytest -x                          # Stop on first failure
uv run pytest --lf                        # Run last failed tests
```

### Code Quality
```bash
uv run ruff check src/                    # Lint code
uv run ruff check src/ --fix             # Auto-fix issues
uv run ruff format src/                   # Format code
uv run mypy src/honk/                     # Type checking
uv run mypy src/honk/notes/              # Type check specific module
```

### Running Scripts
```bash
uv run python script.py                   # Any Python script
uv run python test_notes_setup.py         # Run validation
uv run python demo_notes.py               # Run demo
uv run python -m honk.cli --help         # Run module directly
```

### Dependencies
```bash
uv pip install package                    # Add package
uv pip install -e .                       # Install project in editable mode
uv sync                                   # Sync with uv.lock
uv lock                                   # Update lock file
uv pip list                               # List installed packages
uv pip show package                       # Show package info
```

### Environment Management
```bash
uv venv                                   # Create virtual environment
uv venv --python 3.12                    # Create with specific Python
source .venv/bin/activate                # Activate (if needed)
```

### Tool Management (for honk itself)
```bash
uv tool install --editable .             # Install honk as editable tool
uv tool list --show-paths                # Show installed tools
uv tool uninstall honk                   # Uninstall honk
uv tool upgrade honk                     # Upgrade honk
```

## Why UV?

**Consistency**: Everyone uses Python 3.12.2
**Speed**: 10-100x faster than pip
**Reliability**: Deterministic installs via uv.lock
**Simplicity**: One tool for everything

## Common Mistakes (DON'T DO THIS)

```bash
❌ python script.py                       # Might use wrong Python
❌ pytest                                 # Might use wrong environment
❌ pip install package                    # Installs outside uv
❌ python3 -m pytest                      # Bypasses uv
```

## When NOT to use `uv run`

The `honk` command itself doesn't need `uv run` because it's installed as a tool:

```bash
✅ honk notes edit test.md                # Correct
❌ uv run honk notes edit test.md         # Unnecessary (but won't hurt)
```

But for development tasks, always use `uv run`:

```bash
✅ uv run pytest                          # Correct
❌ pytest                                 # Wrong
```

## Emergency Fixes

### If environment is broken:
```bash
# Nuclear option: delete and recreate
rm -rf .venv
uv venv
uv sync
```

### If uv.lock is corrupted:
```bash
uv lock --upgrade
```

### If imports fail:
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Integration with IDEs

### VS Code
Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

### PyCharm
1. Settings → Project → Python Interpreter
2. Add Interpreter → Existing
3. Select `.venv/bin/python`

## More Info

- UV Docs: https://docs.astral.sh/uv/
- Honk Development Guide: DEVELOPMENT.md
- Agent Instructions: AGENTS.md (Python Environment Standards section)
