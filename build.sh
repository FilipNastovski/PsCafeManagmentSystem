#!/bin/bash
set -e

echo "Building PS Cafe Manager..."

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run: python3 -m venv .venv"
    exit 1
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "Running PyInstaller..."
pyinstaller --clean build.spec

echo ""
echo "Build successful!"
echo "Output: dist/PS-Cafe-Manager/"
