#!/bin/bash
# Quick local validation script - Run before every commit/push!

set -e  # Exit on first error

echo "🧪 Running tests..."
pytest tests/test_server.py -v --tb=short

echo ""
echo "🔍 Running linting..."
ruff check src/ tests/

echo ""
echo "🎨 Checking code formatting..."
black --check src/ tests/

echo ""
echo "📦 Checking import sorting..."
isort --check-only src/ tests/

echo ""
echo "✅ Verifying module imports..."
python -c "import wemo_mcp_server.server; print('✅ Module imports successfully')"

echo ""
echo "✅✅✅ All local checks passed! Safe to commit/push. ✅✅✅"
