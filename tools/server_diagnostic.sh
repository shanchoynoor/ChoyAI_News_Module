#!/bin/bash

# ChoyNewsBot Server Deployment Troubleshooting Script
# Run this on your server to diagnose and fix the Python environment issue

echo "=== ChoyNewsBot Server Deployment Diagnostic ==="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Current Directory: $(pwd)"
echo

echo "=== 1. Checking Virtual Environment ==="
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Virtual environment is active: $VIRTUAL_ENV"
else
    echo "❌ Virtual environment is NOT active"
    echo "Please run: source venv/bin/activate"
fi
echo

echo "=== 2. Checking Python Executables ==="
echo "System python3: $(which python3 2>/dev/null || echo 'NOT FOUND')"
echo "System python: $(which python 2>/dev/null || echo 'NOT FOUND')"
echo "Venv python3: $(ls -la venv/bin/python3 2>/dev/null || echo 'NOT FOUND')"
echo "Venv python: $(ls -la venv/bin/python 2>/dev/null || echo 'NOT FOUND')"
echo

echo "=== 3. Testing Python Versions ==="
if command -v python3 &> /dev/null; then
    echo "python3 version: $(python3 --version)"
else
    echo "❌ python3 not found in PATH"
fi

if command -v python &> /dev/null; then
    echo "python version: $(python --version)"
else
    echo "❌ python not found in PATH"
fi
echo

echo "=== 4. Checking Virtual Environment Directory ==="
if [ -d "venv" ]; then
    echo "✅ venv directory exists"
    echo "Contents of venv/bin/:"
    ls -la venv/bin/ | head -10
else
    echo "❌ venv directory does not exist"
fi
echo

echo "=== 5. Checking choynews executable ==="
if [ -f "bin/choynews" ]; then
    echo "✅ bin/choynews file exists"
    echo "Permissions: $(ls -la bin/choynews)"
    echo "First few lines:"
    head -5 bin/choynews
else
    echo "❌ bin/choynews file does not exist"
fi
echo

echo "=== 6. Suggested Fixes ==="
echo
echo "If venv is missing or corrupted, recreate it:"
echo "  rm -rf venv"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install --upgrade pip"
echo "  pip install -e ."
echo
echo "If python3 is missing from venv/bin, create a symlink:"
echo "  ln -sf $(which python3) venv/bin/python3"
echo
echo "If choynews script fails, try running directly:"
echo "  python3 -m choynews.core.bot"
echo
echo "Alternative: Use python directly instead of shebang:"
echo "  python3 bin/choynews"
echo

echo "=== 7. Environment Variables ==="
echo "PATH: $PATH"
echo "PYTHONPATH: ${PYTHONPATH:-'Not set'}"
echo "VIRTUAL_ENV: ${VIRTUAL_ENV:-'Not set'}"
echo

echo "=== Diagnostic Complete ==="
