# Antifragile Ultra-light RAG POC for TPMs at Loka (Local Only)

## What this is
A tiny, local-first RAG pipeline for Loka TPMs to capture **what went wrong** and turn it into **via-negativa guardrails**.

> "We know a lot more what is wrong than what is right, or, phrased according to the fragile/robust classification, negative knowledge (what is wrong, what does not work) is more robust to error than positive knowledge (what is right, what works) - given that what we know today might turn out to be wrong but what we know to be wrong cannot turn out to be right, at least not easily." ~ Nassim Taleb in Antifragile

The goal of this repo is to be a place where everyone gains from other's mistakes. 

"What kills me, makes others stronger".

## Overview
- Lessons learned, mistakes and errors are authored as **JSON files** via PRs and added into ./data or ./data_ultralight folders.
- Each lesson has/gets a canonical **narrative** (`rag.text`) — ideal for embeddings.
- The build script validates JSON, **writes a `.rag` text file next to each JSON**, and builds a **FAISS** index using **sentence-transformers (local)**.
- No external services required.

## Two flavors of RAG

We now maintain **two parallel scripts** depending on the level of detail you want in your lessons:

- **`rag.py`** → **Full schema**  
  - Richer structure (signals, controls, more metadata).  
  - Best when you want complete, structured lessons with deep context.  
  - Requires more effort from contributors to fill in details.  

- **`rag-ultralight.py`** → **Ultra-light schema**  
  - Minimal fields: title, summary, phase, incident (with impact 1–5), guidance, tags.  
  - Impact is normalized into `{ level: 1..5, description: ... }` automatically.  
  - Always auto-generates `rag.text` if missing.  
  - Designed for quick contribution — lowers the barrier for TPMs.  
  - Ideal for fast capture of “what not to do.”  

Both scripts support the same commands: `validate`, `build-index`, and `query`.

⚠️ Important:
- `rag-ultralight.py` does **not** support `--force-autogen`. Auto-generation is always on because the schema is minimal and always needs enrichment to be useful
- Use `--reset` with either script if you want to **clear and rebuild** the output folder.  
- If you run both systems side-by-side, use **different `--out` directories** (e.g. `./rag_store` vs. `./rag_store_ultralight`) so the indices don’t overwrite each other.

## Repo layout
```
./data                  # TPM-authored lessons (JSON)
./data_ultralight       # ultra-light TPM-authored lessons (JSON)
./rag_store             # RAG index
./rag_store_ultralight  # RAG index for ultra-light version
rag.py                  # full schema RAG pipeline
rag-ultralight.py       # ultra-light schema RAG pipeline
requirements.txt        # install this first
README.md
```

## RAG
Validate all lessons:
```bash
python3 rag.py validate --data ./data
```

Build the store:
```bash
python3 rag.py build-index --data ./data --out ./rag_store --reset --write-back
```

Query it:
```bash
python3 rag.py query --store ./rag_store --q "Kickoff for a biotech client; avoid data mistakes" -k 5
```

## Ultralight RAG Version
Validate all lessons:
```bash
python3 rag-ultralight.py validate --data ./data_ultralight
```

We suggest to keep the ultralight store separate from the most complete one.
Here's how:
```bash
python3 rag-ultralight.py build-index --data ./data_ultralight --out ./rag_store_ultralight --reset --write-back
```

Query it:
```bash
python3 rag-ultralight.py query --store ./rag_store_ultralight --q "Kickoff for a biotech client; avoid data mistakes" -k 5
```

## How you can contribute
1. TPMs submit a JSON file describing something that went wrong or a lesson learned in ./data or ./data_ultralight via a PR.  
2. `validate` ensures schema compliance.  
3. `build-index` ensures `rag.text`, writes `.rag` sidecar, appends normalized record to the store, and builds FAISS index.  
   - With `--write-back`, JSONs are normalized (impact + rag).  
   - With `--reset`, the store folder is cleared before rebuilding.  
4. `query` embeds your question locally and returns the most relevant lessons.

## Notes
- Local embedding model: `sentence-transformers/all-MiniLM-L6-v2` (fast, 384-dim).  
- FAISS index uses inner product on normalized vectors (cosine similarity).  
- You can switch models by passing `--model <name>` to `build-index` and `query`.
