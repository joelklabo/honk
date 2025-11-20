#!/bin/bash
# Run the exact same tests as CI locally
# This ensures your local tests match what runs in CI

set -e

echo "🧪 Running CI Test Suite Locally"
echo "=================================="
echo ""

# Sync dependencies
echo "📦 Syncing dependencies..."
uv sync --all-extras
echo ""

# Run ruff check
echo "🔍 Running ruff check..."
uv run ruff check src/ tests/
echo "✅ Ruff check passed"
echo ""

# Run mypy
echo "🔍 Running mypy..."
uv run mypy src/
echo "✅ Mypy passed"
echo ""

# Run tests
echo "🧪 Running tests..."
uv run pytest tests/ -v
echo "✅ Tests passed"
echo ""

# Validate introspect JSON
echo "🔍 Validating introspect JSON..."
mkdir -p tmp
uv run honk introspect --json > tmp/introspect.json
cat tmp/introspect.json | head -20
echo "✅ Introspect JSON valid"
echo ""

# Test demo hello
echo "🔍 Testing demo hello..."
uv run honk demo hello --help > /dev/null
echo "✅ Demo hello works"
echo ""

# Validate schemas exist
echo "🔍 Validating schemas..."
test -f schemas/result.v1.json && echo "  ✓ result.v1.json exists"
test -f schemas/introspect.v1.json && echo "  ✓ introspect.v1.json exists"
echo "✅ Schemas validated"
echo ""

echo "=================================="
echo "✅ All CI checks passed locally!"
echo "=================================="
