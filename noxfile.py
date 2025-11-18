"""Nox sessions for honk."""
import nox

PYTHON = ".venv/bin/python"


@nox.session(venv_backend="none")
def tests(session):
    """Run the test suite."""
    session.run(PYTHON, "-m", "pytest", "tests/", "-v", external=True)


@nox.session(venv_backend="none")
def ruff(session):
    """Run ruff linter."""
    session.run(PYTHON, "-m", "ruff", "check", "src/", "tests/", external=True)


@nox.session(venv_backend="none")
def mypy(session):
    """Run mypy type checker."""
    session.run(PYTHON, "-m", "mypy", "src/honk/", "--ignore-missing-imports", external=True)


@nox.session(venv_backend="none")
def format(session):
    """Format code with ruff."""
    session.run(PYTHON, "-m", "ruff", "format", "src/", "tests/", external=True)


@nox.session(venv_backend="none")
def format_check(session):
    """Check code formatting."""
    session.run(PYTHON, "-m", "ruff", "format", "--check", "src/", "tests/", external=True)
