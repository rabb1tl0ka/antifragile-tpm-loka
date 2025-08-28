#!/usr/bin/env bash
set -e

echo "🚀 Setting up Antifragile TPM environment..."

# Ensure python3 + venv are available
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3.8+ first."
    exit 1
fi

if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "❌ Python venv not available. Install 'python3-venv' (Debian/Ubuntu: sudo apt install python3-venv)."
    exit 1
fi

# Create virtual environment if not already there
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate venv
echo "🔑 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📚 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️  No requirements.txt found. Skipping dependency install."
fi

echo ""
echo "✅ Setup complete! To start working, run:"
echo "   source .venv/bin/activate"
