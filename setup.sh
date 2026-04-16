#!/bin/bash
# Sci-Literature Setup Script
# Installs dependencies and configures the skill

set -e

echo "==================================="
echo "Sci-Literature v1.0 Setup"
echo "==================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[2/4] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r assets/requirements.txt

# Create config.yaml if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "[3/4] Creating config.yaml..."
    cp assets/config.example.yaml config.yaml
    echo ""
    echo "IMPORTANT: Please edit config.yaml and add your API key!"
    echo "  provider: minimax | zhipu | deepseek | tongyi | moonshot"
    echo "  api_key: YOUR_API_KEY_HERE"
    echo ""
else
    echo "[3/4] config.yaml already exists, skipping..."
fi

# Create output directories
echo "[4/4] Creating output directories..."
mkdir -p my_pdfs
mkdir -p extracted

echo ""
echo "==================================="
echo "Setup complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml with your API key"
echo "  2. Add PDF files to my_pdfs/"
echo "  3. Run: python scripts/tool.py all --folder ./my_pdfs --output ./extracted"
echo ""
echo "Or for interactive use in opencode/claude/openclaw,"
echo "the skill will auto-load when you ask literature questions."
echo ""