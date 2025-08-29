#!/usr/bin/env bash
set -e

echo "🚀 Running Antifragile TPM Ultralight Demo..."

# Activate local virtual environment if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Step 1: Validate data
echo "🔍 Validating data in ./data_ultralight..."
python3 rag-ultralight.py validate --data ./data_ultralight

# Step 2: Build index
echo "📦 Building ultralight index into ./rag_store_ultralight..."
python3 rag-ultralight.py build-index --data ./data_ultralight --out ./rag_store_ultralight --reset --write-back

# Step 3: Run query
echo "💡 Querying demo store..."
python3 rag-ultralight.py query --store ./rag_store_ultralight --q "Kickoff for a biotech client; avoid data mistakes" -k 5

echo ""
echo "✅ Demo finished!"
