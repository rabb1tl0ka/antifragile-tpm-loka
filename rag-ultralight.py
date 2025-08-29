#!/usr/bin/env python3
"""
rag-ultralight.py
Ultra-light RAG for 'via negativa' lessons.

- Parses a simplified JSON format.
- Ensures a retrieval-ready rag block with auto-built text.
- Requires `incident.impact` to be an object: { level: 1..5, description: string }.
- Builds FAISS index and supports query.

Usage:
  python3 rag-ultralight.py validate --data ./data
  python3 rag-ultralight.py build-index --data ./data --out ./rag_store --write-back
  python3 rag-ultralight.py query --store ./rag_store --q "Kickoff alignment for healthcare POC" -k 5
"""
import argparse
import json
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------- UltraLight defaults ----------
IMPACT_MAP = {
    1: "Minor – little to no impact on timeline or client",
    2: "Low – some rework needed, but contained",
    3: "Moderate – noticeable delays or frustration",
    4: "Severe – major delays, significant client dissatisfaction",
    5: "Critical – project failure or client loss",
}

# A permissive schema: we keep just the essentials and allow additionalProperties.
DEFAULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Loka Antifragile UltraLight Lesson",
    "type": "object",
    "required": ["id", "title", "summary", "phase", "industries", "incident", "guidance", "tags"],
    "properties": {
        "id": {"type": "string", "minLength": 4},
        "title": {"type": "string", "minLength": 6},
        "summary": {"type": "string", "minLength": 20},
        "phase": {"type": "string"},
        "client_name": {"type": "string"},
        "industries": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "project_type": {"type": "string"},
        
"incident": {
            "type": "object",
            "required": ["what_happened", "root_cause", "root_cause_category", "impact"],
            "properties": {
                "what_happened": {"type": "string", "minLength": 20},
                "root_cause": {"type": "string", "minLength": 10},
                "root_cause_category": {"type": "string"},
                "impact": {
                    "type": "object",
                    "required": ["level", "description"],
                    "properties": {
                        "level": {"type": "integer", "minimum": 1, "maximum": 5},
                        "description": {"type": "string", "minLength": 3}
                    },
                    "additionalProperties": True
                }
            },
            "additionalProperties": True
        },
        "guidance":
 {
            "type": "object",
            "required": ["do_not_do", "do_instead"],
            "properties": {
                "do_not_do": {"type": "string", "minLength": 10},
                "do_instead": {"type": "string", "minLength": 10},
            },
            "additionalProperties": True,
        },
        "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "created_at": {"type": "string"},
        "author": {"type": "string"},
        "rag": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "minLength": 50},
                "meta": {"type": "object"},
            },
            "additionalProperties": True,
        },
    },
    "additionalProperties": True,
}

# ---------- utils ----------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def iter_json_files(root: Path) -> List[Path]:
    return sorted([p for p in root.rglob("*.json") if p.is_file()])

def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, obj: Dict[str, Any]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def append_jsonl(path: Path, obj: Dict[str, Any]):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def validate_json(doc: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        from jsonschema import Draft7Validator
    except ImportError:
        return False, "jsonschema not installed (pip install jsonschema)"
    v = Draft7Validator(schema)
    errors = sorted(v.iter_errors(doc), key=lambda e: e.path)
    if not errors:
        return True, ""
    msgs = []
    for e in errors:
        where = "/".join(map(str, e.path))
        msgs.append(f" - {where or '$'}: {e.message}")
    return False, "\n".join(msgs)

def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


    impact = incident.get("impact")
    impact_desc = incident.get("impact_description")

    if isinstance(impact, int):
        level = max(1, min(5, impact))
        desc = impact_desc or IMPACT_MAP.get(level, "")
        incident["impact"] = {"level": level, "description": desc}
    elif isinstance(impact, dict):
        level = impact.get("level")
        if isinstance(level, int) and 1 <= level <= 5:
            if not impact.get("description"):
                impact["description"] = impact_desc or IMPACT_MAP.get(level, "")
        else:
            # If invalid level, try to coerce from impact_desc keywords; else default to 3
            level = 3
            impact["level"] = level
            impact["description"] = impact.get("description") or impact_desc or IMPACT_MAP[level]
        incident["impact"] = impact
    else:
        # No impact provided -> default moderate
        incident["impact"] = {"level": 3, "description": IMPACT_MAP[3]}
    return incident

def ensure_provenance(d: Dict[str, Any]) -> Dict[str, Any]:
    if "created_at" not in d or not isinstance(d["created_at"], str) or len(d["created_at"]) < 10:
        d["created_at"] = now_iso()
    if "author" not in d:
        d["author"] = ""
    return d

def build_rag_text(d: Dict[str, Any]) -> str:
    """
    Compose a short narrative from the UltraLight fields.
    """
    title = d.get("title", "")
    summary = d.get("summary", "")
    phase = d.get("phase", "")
    client = d.get("client_name", "")
    industries = ", ".join(_as_list(d.get("industries")))
    proj_type = d.get("project_type", "")
    incident = d.get("incident", {}) if isinstance(d.get("incident"), dict) else {}
    what = incident.get("what_happened", "")
    root_cause = incident.get("root_cause", "")
    root_cat = incident.get("root_cause_category", "")
    impact_obj = incident.get("impact", {})
    impact_level = impact_obj.get("level") if isinstance(impact_obj, dict) else None
    impact_desc = impact_obj.get("description") if isinstance(impact_obj, dict) else None
    guidance = d.get("guidance", {}) if isinstance(d.get("guidance"), dict) else {}
    do_not = guidance.get("do_not_do", "")
    do_instead = guidance.get("do_instead", "")

    bits: List[str] = []
    if title: bits.append(f"Lesson: {title}.")
    if summary: bits.append(f"Summary: {summary}")
    ctx_parts = [f"phase={phase}" if phase else "", f"client={client}" if client else "",
                 f"industries={industries}" if industries else "", f"type={proj_type}" if proj_type else ""]
    ctx = ", ".join([x for x in ctx_parts if x])
    if ctx: bits.append(f"Context: {ctx}.")
    if what: bits.append(f"What happened: {what}")
    if root_cause or root_cat:
        cat = f" (category: {root_cat})" if root_cat else ""
        bits.append(f"Root cause: {root_cause}{cat}")
    if impact_level or impact_desc:
        lvl = f"level={impact_level}" if impact_level else ""
        desc = impact_desc or (IMPACT_MAP.get(impact_level) if impact_level else "")
        phr = ", ".join([p for p in [lvl, desc] if p])
        if phr:
            bits.append(f"Impact: {phr}.")
    if do_not: bits.append(f"Do NOT: {do_not}")
    if do_instead: bits.append(f"Do instead: {do_instead}")
    text = " ".join(bits).strip()

    # Pad lightly to help embeddings if too short
    if len(text) < 160:
        text += " This lesson highlights the value of early stakeholder alignment, shared success criteria, and explicit definitions of done."
    return text

def ensure_rag(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize document to include:
      - incident.impact already valid per schema
      - rag.text (auto-generated if missing)
      - rag.meta with a tiny set of helpful fields
    """
    c = dict(d)
    ensure_provenance(c)

    # incident.impact is assumed valid per schema (level + description)

    # Ensure rag.text
    rag = c.get("rag") if isinstance(c.get("rag"), dict) else {}
    text = rag.get("text") if isinstance(rag.get("text"), str) else ""
    if not text:
        text = build_rag_text(c)

    # Light meta (kept very small)
    meta = {
        "phase": c.get("phase", ""),
        "industries": _as_list(c.get("industries")),
        "tags": _as_list(c.get("tags")),
        "created_at": c.get("created_at"),
        "author": c.get("author", ""),
    }
    c["rag"] = {"text": text, "meta": meta}
    return c

def write_sidecar(json_path: Path, text: str):
    with open(json_path.with_suffix(".rag"), "w", encoding="utf-8") as f:
        f.write(text)

# ---------- index ----------
class Embedder:
    def __init__(self, model: str):
        self.model_name = model
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError:
            raise RuntimeError("Please install sentence-transformers")
        self.model = SentenceTransformer(model)

    def embed(self, texts: List[str]):
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

def build_faiss_index(vectors, out_dir: Path):
    try:
        import faiss  # type: ignore
    except ImportError:
        raise RuntimeError("Please install faiss-cpu")
    import numpy as np
    vecs = vectors.astype("float32")
    d = vecs.shape[1]
    faiss.normalize_L2(vecs)
    index = faiss.IndexFlatIP(d)
    index.add(vecs)
    faiss.write_index(index, str(out_dir / "index.faiss"))

# ---------- commands ----------
def cmd_validate(args):
    data_dir = Path(args.data)
    schema = DEFAULT_SCHEMA if not args.schema else load_json(Path(args.schema))
    files = iter_json_files(data_dir)
    if not files:
        print(f"No JSON files found under {data_dir}")
        return 1
    bad = 0
    for p in files:
        doc = load_json(p)
        ok, msg = validate_json(doc, schema)
        if ok:
            print(f"✅ {p}")
        else:
            print(f"⚠️  {p}\n{msg}\n")
            bad += 1
    if bad:
        print(f"{bad} file(s) failed validation.")
        return 2
    return 0

def cmd_build_index(args):
    data_dir = Path(args.data)
    out_dir = Path(args.out)

    if args.reset and out_dir.exists():
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = out_dir / "chunks.jsonl"
    ids_path = out_dir / "ids.jsonl"

    files = iter_json_files(data_dir)
    if not files:
        print(f"No JSON files found under {data_dir}")
        return 1

    texts, ids, titles, paths = [], [], [], []
    for p in files:
        doc = load_json(p)
        doc = ensure_rag(doc)

        # optional write-back to persist normalized impact + rag
        if args.write_back:
            try:
                save_json(p, doc)
            except Exception as e:
                print(f"⚠️  Write-back failed for {p}: {e}")

        # sidecar .rag
        write_sidecar(p, doc["rag"]["text"])

        rec = {
            "id": doc.get("id", ""),
            "path": str(p),
            "title": doc.get("title", ""),
            "phase": doc.get("phase", ""),
            "industries": doc.get("industries", []),
            "tags": doc.get("tags", []),
            "rag_text": doc["rag"]["text"],
        }
        append_jsonl(chunks_path, rec)
        append_jsonl(ids_path, {"id": rec["id"], "path": rec["path"], "title": rec["title"]})

        texts.append(doc["rag"]["text"])
        ids.append(rec["id"])
        titles.append(rec["title"])
        paths.append(rec["path"])

    # Embed + index
    embedder = Embedder(model=args.model)
    vecs = embedder.embed(texts)
    build_faiss_index(vecs, out_dir)

    meta = {
        "created_at": now_iso(),
        "num_items": len(texts),
        "embedder": "sbert",
        "model": args.model,
    }
    save_json(out_dir / "meta.json", meta)
    print(f"✅ Built store at {out_dir} with {len(texts)} items.")
    return 0

def cmd_query(args):
    try:
        import faiss  # type: ignore
    except ImportError:
        raise RuntimeError("Please install faiss-cpu")
    import numpy as np

    store = Path(args.store)
    index_path = store / "index.faiss"
    ids_path = store / "ids.jsonl"
    if not index_path.exists():
        raise RuntimeError(f"Missing index at {index_path}. Run build-index first.")

    # Load ids/titles/paths
    ids, titles, paths = [], [], []
    with open(ids_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ids.append(rec.get("id", ""))
            titles.append(rec.get("title", ""))
            paths.append(rec.get("path", ""))

    # Embed query
    embedder = Embedder(model=args.model)
    xq = embedder.embed([args.q]).astype("float32")
    faiss.normalize_L2(xq)

    index = faiss.read_index(str(index_path))
    k = max(1, args.k)

    # If user sent --pool, fall back to heuristic max(k*4, 20).
    # Else, if there's no --pool, respect their choice but ensure it's never < k.
    # (We do NOT force k*4 here because an explicit --pool is considered intentional.)
    if args.pool is None:
        pool = max(k * 4, 20)
    else:
        pool = max(k, args.pool)

    D, I = index.search(xq, pool)

    # Impact-aware re-ranking: semantic first, impact as a gentle nudge
    slope = float(args.impact_slope)
    candidates = []
    for dist, idx in zip(D[0], I[0]):
        if idx == -1:
            continue
        try:
            with open(paths[idx], "r", encoding="utf-8") as f:
                doc = json.load(f)
            impact_level = int(doc.get("incident", {}).get("impact", {}).get("level", 3))
        except Exception:
            impact_level = 3

        adjusted = float(dist) * (1.0 + slope * (impact_level - 3))
        candidates.append({
            "idx": int(idx),
            "title": titles[idx],
            "id": ids[idx],
            "path": paths[idx],
            "cosine": float(dist),
            "impact": impact_level,
            "adjusted": adjusted,
        })

    # Re-rank by adjusted score and keep top-k
    candidates.sort(key=lambda r: r["adjusted"], reverse=True)
    top = candidates[:k]

    print(f"\nTop {k} results for: {args.q}")
    print(f"(using impact-slope={slope}, pool={pool})\n")
    for rank, r in enumerate(top, start=1):
        print(f"{rank}. {r['title']}  (adj={r['adjusted']:.4f} | cos={r['cosine']:.4f} | impact={r['impact']})")
        print(f"   id: {r['id']}")
        print(f"   file: {r['path']}\n")

        # Print guidance fields
        try:
            with open(r['path'], "r", encoding="utf-8") as f:
                doc = json.load(f)
            g = doc.get("guidance", {})
            if g:
                do_not = g.get("do_not_do", "")
                do_instead = g.get("do_instead", "")
                if do_not:
                    print(f"   ❌ Do NOT: {do_not}")
                if do_instead:
                    print(f"   ✅ Do instead: {do_instead}")
        except Exception as e:
            print(f"   ⚠️ Could not load guidance: {e}")

        print()  # blank line after each result

# ---------- main ----------
def main():
    p = argparse.ArgumentParser(description="UltraLight Lessons RAG")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate (permissively) UltraLight JSON files")
    v.add_argument("--data", required=True, help="Directory with *.json lesson files")
    v.add_argument("--schema", help="Optional: path to a custom schema JSON")
    v.set_defaults(func=cmd_validate)

    b = sub.add_parser("build-index", help="Build FAISS index from UltraLight JSON files")
    b.add_argument("--data", required=True, help="Directory with *.json lesson files")
    b.add_argument("--out", required=True, help="Output directory for store")
    b.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="SBERT model")
    b.add_argument("--write-back", action="store_true", help="Persist normalized impact + rag back to source JSONs")
    b.add_argument("--reset", action="store_true", help="Reset (delete + rebuild) the output folder before building index")
    b.set_defaults(func=cmd_build_index)

    q = sub.add_parser("query", help="Query the store with a natural-language prompt")
    q.add_argument("--store", required=True, help="Path to store directory created by build-index")
    q.add_argument("--q", required=True, help="Natural language query")
    q.add_argument("-k", type=int, default=5, help="Top-k results")
    q.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    q.add_argument("--impact-slope", type=float, default=0.10, help="Re-ranking slope for impact weighting (e.g., 0.1)")
    q.add_argument("--pool", type=int, default=None, help="Candidate pool size for re-ranking (default = max(k*4, 20))")

    q.set_defaults(func=cmd_query)

    args = p.parse_args()
    try:
        rc = args.func(args)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        rc = 1
    sys.exit(rc)

if __name__ == "__main__":
    main()
