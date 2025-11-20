# Honk 🪿

**Agent-first CLI for developer workflows** - Standardizes automation flows with doctor packs, authentication, and structured result envelopes.

## Quick Start

### Prerequisites

- Python 3.12 or later
- `uv` package manager (see installation below)

### Installing UV

If you don't have `uv` installed, install it with pip:

```bash
pip install uv
```

Or on macOS/Linux with the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For other installation methods, see the [UV documentation](https://docs.astral.sh/uv/).

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/joelklabo/honk.git
   cd honk
   ```

2. **Sync dependencies:**
   ```bash
   # Install production dependencies
   uv sync
   
   # Install with development dependencies (for testing/linting)
   uv sync --extra dev
   ```

3. **Verify installation:**
   ```bash
   uv run python -m honk.cli --help
   ```

### Running the Program

Honk uses `uv run` for all Python operations to ensure consistent environments:

```bash
# Show help
uv run python -m honk.cli --help

# Run demo command
uv run python -m honk.cli demo hello

# Get version
uv run python -m honk.cli version

# List all commands with metadata
uv run python -m honk.cli introspect --json
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_cli.py

# Run tests matching a pattern
uv run pytest -k "test_demo"

# Run with coverage
uv run pytest --cov=src/honk --cov-report=term-missing

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf
```

### Code Quality

```bash
# Lint code
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check src/ --fix

# Format code
uv run ruff format src/

# Type checking
uv run mypy src/honk/
```

## Project Structure

```
.
├── .github/
│   ├── agents/              # Custom GitHub Copilot agents
│   └── workflows/           # CI/CD workflows
├── docs/
│   ├── agents.md            # AI agent instructions (source of truth)
│   ├── spec.md              # Architecture specification
│   ├── DEVELOPMENT.md       # Development guide
│   ├── plans/
│   │   └── main.md          # Work tracking document
│   └── references/          # Documentation, research, notes
├── src/honk/
│   ├── cli.py               # Main CLI entry point
│   ├── result.py            # Result envelope models
│   ├── auth/                # Authentication subsystem
│   ├── demo/                # Demo commands
│   ├── internal/            # Shared systems (doctor, logging)
│   ├── notes/               # AI-assisted note-taking
│   ├── release/             # Release automation
│   ├── system/              # System diagnostics
│   ├── tools/agent/         # Agent management tools
│   └── watchdog/            # System health monitoring
├── tests/                   # Test suite
├── schemas/                 # JSON schemas for validation
├── pyproject.toml           # Project metadata and dependencies
└── uv.lock                  # Locked dependencies
```

## Available Commands

### Core Commands

- `honk demo hello` - Demo greeting command (exercises shared scaffolding)
- `honk doctor` - Run doctor packs to check prerequisites
- `honk introspect` - Emit command catalog with metadata
- `honk version` - Show version information
- `honk info` - Show CLI information

### Authentication

- `honk auth gh status` - Check GitHub authentication status
- `honk auth gh login` - Login to GitHub
- `honk auth az status` - Check Azure DevOps authentication status
- `honk auth az login` - Login to Azure DevOps

### Agent Management

- `honk agent scaffold create` - Create a new GitHub Copilot custom agent
- `honk agent validate` - Validate agent YAML frontmatter
- `honk agent list` - List all available custom agents

### System Monitoring

- `honk system procs` - List running processes
- `honk system disk` - Show disk usage
- `honk system network` - Show network status

### Watchdog

- `honk watchdog pty show` - Show PTY status
- `honk watchdog pty clean` - Clean up PTY leaks
- `honk watchdog pty watch` - Continuous PTY monitoring

### Notes (AI-assisted note-taking)

- `honk notes edit <file>` - Edit notes with AI assistance
- `honk notes organize` - Organize notes using AI
- `honk notes config` - Show notes configuration

### Release Automation

- `honk release analyze` - Analyze commits for release
- `honk release version bump` - Bump version
- `honk release changelog generate` - Generate changelog

## Development Workflow

### Python Environment Standards

**⚠️ CRITICAL: Always use `uv run` for ALL Python operations in this project.**

**DO:**
```bash
✅ uv run python script.py          # Run Python scripts
✅ uv run pytest                     # Run tests
✅ uv run mypy src/                  # Type checking
✅ uv run ruff check src/            # Linting
```

**DON'T:**
```bash
❌ python script.py                  # Might use wrong Python version
❌ pytest                            # Might use wrong environment
❌ pip install package               # Installs outside uv
```

### Why UV?

- **Consistency**: Everyone uses Python 3.12.2
- **Speed**: 10-100x faster than pip
- **Reliability**: Deterministic installs via `uv.lock`
- **Simplicity**: One tool for everything

### Adding Dependencies

```bash
# Add a production dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Sync after adding
uv sync
```

### Making Changes

1. Create a feature branch
2. Make your changes
3. Run tests: `uv run pytest`
4. Run linting: `uv run ruff check src/`
5. Run type checking: `uv run mypy src/honk/`
6. Commit your changes
7. Open a pull request

## Architecture

Honk follows an **agent-first** design philosophy:

- **Result Envelopes**: Every command returns structured JSON with `status`, `facts`, `links`, and `next` steps
- **Doctor Packs**: Prerequisite checking framework (global, auth-gh, auth-az)
- **Authentication**: Centralized auth management for GitHub and Azure DevOps
- **Introspection**: Full command catalog available via `honk introspect --json`

### CLI Grammar

Commands follow a consistent three-level hierarchy:

```
honk <area> <tool> <action>
```

Examples:
- `honk demo hello`
- `honk auth gh login`
- `honk watchdog pty show`

### Exit Codes

- `0` - Success (ok)
- `10` - Prerequisite failed (prereq_failed)
- `11` - Needs authentication (needs_auth)
- `12` - Token expired (token_expired)
- `20` - Network error
- `30` - System error
- `50` - Internal bug
- `60` - Rate limited

## Documentation

- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development guide and editable install instructions
- **[spec.md](docs/spec.md)** - Complete architecture specification
- **[agents.md](docs/agents.md)** - AI agent instructions (also symlinked as AGENTS.md, CLAUDE.md, GEMINI.md)
- **[plans/main.md](docs/plans/main.md)** - Current work tracking
- **[uv-quick-reference.md](docs/uv-quick-reference.md)** - UV command reference

## Common Issues

### If environment is broken

```bash
# Nuclear option: delete and recreate
rm -rf .venv
uv venv
uv sync --extra dev
```

### If imports fail

```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Tech Stack

- **Python 3.12.2** managed via uv 0.4.20
- **CLI Framework**: Typer 0.12.3 + Rich 13.7.1 for UX
- **TUI (optional)**: Textual 0.61.0
- **Data Validation**: Pydantic 2.8.2 + jsonschema 4.23.0
- **HTTP**: HTTPX 0.27.2
- **Testing**: pytest 8.3.3, pytest-xdist 3.6.1, respx 0.21.1
- **Code Quality**: ruff 0.6.9, mypy 1.11.2
- **Build**: nox 2024.4.15

## Contributing

1. Read [DEVELOPMENT.md](docs/DEVELOPMENT.md) for development workflow
2. Follow the coding standards in [agents.md](docs/agents.md)
3. Write tests for new features (TDD approach)
4. Ensure all tests pass and code is linted
5. Update documentation as needed

## License

[Add license information here]

## Support

- GitHub Issues: [https://github.com/joelklabo/honk/issues](https://github.com/joelklabo/honk/issues)
- Documentation: See `docs/` directory
