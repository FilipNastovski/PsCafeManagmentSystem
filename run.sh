#!/bin/bash
# Run script for PlayStation Management System on Linux Mint
# Usage: ./run.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$SCRIPT_DIR"

echo "Starting PS Café Management System..."

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
fi

python main.py

deactivate