#!/usr/bin/env bash
set -e

echo "🚀 Running Antifragile TPM Demo..."

# Activate local virtual environment if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Step 1: Validate data
echo "🔍 Validating data in ./data..."
python3 rag.py validate --data ./data

# Step 2: Build index
echo "📦 Building ultralight index into ./datarag_store..."
python3 rag.py build-index --data ./data --out ./datarag_store --reset --write-back

# Step 3: Run query
echo "💡 Querying demo store..."
python3 rag.py query --store ./datarag_store --q "Kickoff for a biotech client; avoid data mistakes" -k 5

echo ""
echo "✅ Demo finished!"
