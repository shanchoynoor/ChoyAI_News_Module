#!/bin/bash
# Commands to run on your server to fix the virtual environment

echo "=== ChoyNewsBot Server Fix Commands ==="
echo "Run these commands on your server step by step:"
echo

echo "1. First, check what's in your venv/bin directory:"
echo "   ls -la venv/bin/"
echo

echo "2. Check if python3 is installed on the system:"
echo "   which python3"
echo "   python3 --version"
echo

echo "3. If python3 is missing, install it:"
echo "   sudo apt update"
echo "   sudo apt install -y python3 python3-pip python3-venv"
echo

echo "4. Recreate the virtual environment:"
echo "   rm -rf venv"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo

echo "5. Install the package:"
echo "   pip install --upgrade pip"
echo "   pip install -e ."
echo

echo "6. Test the installation:"
echo "   python3 -c \"import choynews; print('✅ Success')\"" 
echo

echo "7. Try running the bot:"
echo "   python3 -m choynews.core.bot"
echo

echo "=== Alternative Quick Fix ==="
echo "If the above doesn't work, try this direct approach:"
echo "   source venv/bin/activate"
echo "   python3 -m choynews.core.bot"
echo

echo "=== If venv is completely broken ==="
echo "   deactivate  # Exit current venv"
echo "   rm -rf venv  # Remove broken venv"
echo "   python3 -m venv venv  # Create new venv"
echo "   source venv/bin/activate  # Activate new venv"
echo "   pip install --upgrade pip"
echo "   pip install -e .  # Install package"
echo "   python3 -m choynews.core.bot  # Run bot"
