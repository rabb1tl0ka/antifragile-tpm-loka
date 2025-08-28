#!/usr/bin/env python3
"""
antifragile_build_index.py
Ultra-light RAG POC for "via negativa" lessons.
- Validates JSON files against the lesson_case schema (embedded here as DEFAULT_SCHEMA).
- Ensures a canonical rag.text is present (auto-composes if missing).
- Writes a .rag text file NEXT TO each JSON lesson (same basename, .rag extension).
- Appends normalized records to a JSONL ("chunks.jsonl").
- Builds a FAISS vector index over rag.text using sentence-transformers (local).
- Provides a simple `query` command to retrieve top-k similar lessons.

Usage examples:
  python antifragile_build_index.py validate --data ./data
  python antifragile_build_index.py build-index --data ./data --out ./rag_store
  python antifragile_build_index.py query --store ./rag_store --q "Kickoff for a biotech client; avoid data mistakes" -k 5
"""
import argparse
import json
import sys
import shutil
from datetime import date, datetime, UTC
from pathlib import Path
from typing import List, Dict, Any, Tuple

# --- Embedded default JSON Schema (draft-07) ---
DEFAULT_SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://loka.example/schema/lesson_case.schema.json",
  "title": "Loka Antifragile Lesson Case",
  "type": "object",
  "required": [
    "id","title","summary","phase","area","industries","severity","confidence",
    "evidence_strength","guidance","incident","impact","signals","controls",
    "evidence","tags","authorship","rag","created_at","updated_at"
  ],
  "properties": {
    "id": {"type":"string","pattern":"^[0-9a-fA-F-]{36}$"},
    "title":{"type":"string","minLength":8,"maxLength":200},
    "summary":{"type":"string","minLength":40},
    "phase":{"type":"string","enum":["Discovery","Kickoff","Design","Build","Test","Deploy","Operate","Closeout"]},
    "area":{"type":"string","enum":["Scope","Communication","Estimation","Staffing","Data","Infra","Security","Compliance","QA","MLOps","DevOps","Architecture","Vendor","Finance","Legal"]},
    "industries":{"type":"array","items":{"type":"string"},"minItems":1},
    "severity":{"type":"string","enum":["P1","P2","P3","P4"]},
    "confidence":{"type":"integer","minimum":1,"maximum":5},
    "evidence_strength":{"type":"string","enum":["Anecdote","Multiple cases","Quant-backed"]},
    "lesson_type":{"type":"string","enum":["Premature Implementation","Scope Churn","Hidden Dependency","Understaffed","Data Contract Gap","Estimation Miss","Environment Drift","Stakeholder Misalignment","Ownership Ambiguity","Other"],"default":"Other"},
    "guidance":{
      "type":"object","required":["do_not_do","do_instead","checklists"],
      "properties":{
        "do_not_do":{"type":"string","minLength":20},
        "do_instead":{"type":"string","minLength":20},
        "checklists":{"type":"array","items":{"type":"string","minLength":3},"minItems":1}
      }
    },
    "incident":{
      "type":"object","required":["context","what_happened","root_cause","root_cause_category","timeline"],
      "properties":{
        "context":{
          "type":"object","required":["project_goal","client_profile"],
          "properties":{
            "project_goal":{"type":"string"},
            "client_profile":{
              "type":"object","required":["industry","size","delivery_model"],
              "properties":{
                "industry":{"type":"string"},
                "size":{"type":"string","enum":["Startup","SMB","Mid-Market","Enterprise"]},
                "delivery_model":{"type":"string","enum":["T&M","Fixed Bid","Retainer","Other"]}
              },"additionalProperties":False
            }
          },"additionalProperties":True
        },
        "what_happened":{"type":"string","minLength":40},
        "root_cause":{"type":"string","minLength":20},
        "root_cause_category":{"type":"string","enum":["Unclear Scope","Missing Data Contract","Staffing Gap","Dependency Risk","Estimation Error","Process Gap","Technical Debt","Ownership Gap", "Stakeholder Misalignment","Other"]},
        "timeline":{"type":"object","required":["start","end"],"properties":{"start":{"type":"string","format":"date"},"end":{"type":"string","format":"date"}}}
      }
    },
    "impact":{
      "type":"object","required":["time_hours","cost_currency","quality","client_sentiment_before","client_sentiment_after","mttd_hours","mttr_hours"],
      "properties":{
        "time_hours":{"type":"number","minimum":0},
        "cost_currency":{"type":"object","required":["amount","currency"],"properties":{"amount":{"type":"number","minimum":0},"currency":{"type":"string","default":"USD"}}},
        "quality":{"type":"string"},
        "client_sentiment_before":{"type":"integer","minimum":-5,"maximum":5},
        "client_sentiment_after":{"type":"integer","minimum":-5,"maximum":5},
        "mttd_hours":{"type":"number","minimum":0},
        "mttr_hours":{"type":"number","minimum":0}
      }
    },
    "signals":{"type":"array","items":{"type":"string","minLength":3},"minItems":1},
    "controls":{"type":"array","items":{"type":"object","required":["name","kind"],"properties":{"name":{"type":"string"},"kind":{"type":"string","enum":["preventative","detective","corrective"]},"is_automatable":{"type":"boolean","default":False}}},"minItems":1},
    "evidence":{"type":"array","items":{"type":"object","required":["kind","title","url_or_path","confidentiality"],"properties":{"kind":{"type":"string","enum":["Doc","Slide","Jira","Slack","Email","Recording","PMNote","Other"]},"title":{"type":"string"},"url_or_path":{"type":"string"},"confidentiality":{"type":"string","enum":["Public","Internal","Restricted"]}}}},
    "tags":{"type":"array","items":{"type":"string"},"minItems":1},
    "authorship":{"type":"object","required":["authors"],"properties":{"authors":{"type":"array","items":{"type":"object","required":["display","role","org"],"properties":{"display":{"type":"string"},"role":{"type":"string"},"org":{"type":"string","enum":["Loka","Client","Other"],"default":"Loka"}}},"minItems":1},"review":{"type":"object","required":["status"],"properties":{"status":{"type":"string","enum":["draft","in_review","approved","changes_requested"]},"reviewer":{"type":"string"},"notes":{"type":"string"},"date":{"type":"string","format":"date"}}}}},
    "confidentiality":{"type":"string","enum":["Public","Internal","Restricted"],"default":"Internal"},
    "rag":{"type":"object","required":["text","meta"],"properties":{"text":{"type":"string","minLength":200},"meta":{"type":"object","required":["phase","area","industries","severity","tags","first_validated","last_validated"],"properties":{"phase":{"type":"string"},"area":{"type":"string"},"industries":{"type":"array","items":{"type":"string"}},"severity":{"type":"string"},"tags":{"type":"array","items":{"type":"string"}},"first_validated":{"type":"string","format":"date"},"last_validated":{"type":"string","format":"date"},"project_size":{"type":"string","enum":["XS","S","M","L","XL"],"default":"M"},"team_composition":{"type":"string"},"delivery_model":{"type":"string"}},"additionalProperties":True}}},
    "created_at":{"type":"string","format":"date-time"},
    "updated_at":{"type":"string","format":"date-time"},
    "version":{"type":"string","pattern":"^[0-9]+\\.[0-9]+\\.[0-9]+$","default":"1.0.0"}
  },
  "additionalProperties": False
}

# --- utilities ---
def iter_json_files(root: Path) -> List[Path]:
    return sorted([p for p in root.rglob("*.json") if p.is_file()])

def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def append_jsonl(path: Path, obj: Dict[str, Any]):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def validate_json(doc: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        from jsonschema import Draft7Validator
    except ImportError:
        print("Please install jsonschema: pip install jsonschema")
        return False, "jsonschema not installed"
    v = Draft7Validator(schema)
    errors = sorted(v.iter_errors(doc), key=lambda e: e.path)
    if not errors:
        return True, ""
    msgs = []
    for e in errors:
        where = "/".join(map(str, e.path))
        msgs.append(f" - {where or '$'}: {e.message}")
    return False, "\n".join(msgs)

# --- RAG text builder (existing logic you already had) ---
def build_rag_text(d: Dict[str, Any]) -> str:
    """Compose a narrative rag.text from canonical fields."""
    title = d.get("title","")
    summary = d.get("summary","")
    phase = d.get("phase","")
    area = d.get("area","")
    industries = ", ".join(d.get("industries",[]))
    severity = d.get("severity","")
    what = d.get("incident",{}).get("what_happened","")
    root_cause = d.get("incident",{}).get("root_cause","")
    root_cat = d.get("incident",{}).get("root_cause_category","")
    impact = d.get("impact",{})
    time_hours = impact.get("time_hours")
    cost = impact.get("cost_currency",{}).get("amount")
    ccy = impact.get("cost_currency",{}).get("currency","USD")
    csb = impact.get("client_sentiment_before")
    csa = impact.get("client_sentiment_after")
    do_not = d.get("guidance",{}).get("do_not_do","")
    do_instead = d.get("guidance",{}).get("do_instead","")
    checks = d.get("guidance",{}).get("checklists",[])

    bits: List[str] = []
    if title: bits.append(f"Lesson: {title}.")
    if summary: bits.append(f"Summary: {summary}")
    meta = ", ".join([x for x in [
        f"phase={phase}" if phase else "",
        f"area={area}" if area else "",
        f"industries={industries}" if industries else "",
        f"severity={severity}" if severity else "",
    ] if x])
    if meta: bits.append(f"Context: {meta}.")
    if what: bits.append(f"What happened: {what}")
    if root_cause or root_cat:
        cat = f"(category: {root_cat})" if root_cat else ""
        bits.append(f"Root cause: {root_cause} {cat}".strip())
    imp = []
    if time_hours is not None: imp.append(f"time_impact≈{time_hours}h")
    if cost is not None: imp.append(f"cost≈{cost} {ccy}")
    if csb is not None and csa is not None: imp.append(f"client_sentiment {csb}→{csa}")
    if imp: bits.append("Impact: " + ", ".join(imp) + ".")
    if do_not: bits.append(f"Do NOT: {do_not}")
    if do_instead: bits.append(f"Do instead: {do_instead}")
    if checks: bits.append("Checks: " + "; ".join(checks) + ".")
    txt = " ".join(bits).strip()
    if len(txt) < 200:
        txt += " This case emphasizes preventing recurrence via clear stakeholder alignment, early risk surfacing, and explicit definitions of done."
    return txt

# --- NEW: ensure_rag wrapper + generator ---
def ensure_rag_text(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backwards-compatible helper (kept for callers).
    Prefer ensure_rag(..., force=...) below which guarantees schema-required fields
    and a min length for rag.text.
    """
    return ensure_rag(d, force=False)

def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def ensure_rag(case: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    """
    Ensure a retrieval-ready rag block exists and meets schema:
      - builds/refreshes rag.text (>= 200 chars) from canonical fields
      - mirrors required meta fields and dates
    """
    c = dict(case)  # shallow copy
    rag = c.get("rag") if isinstance(c.get("rag"), dict) else {}
    meta = rag.get("meta") if isinstance(rag.get("meta"), dict) else {}

    # --- Build/refresh rag.text when forced or missing/short
    text = rag.get("text") if isinstance(rag.get("text"), str) else ""
    if force or not text:
        text = build_rag_text(c)
    if len(text) < 200:
        # pad with a compact recap to meet the schema + help embeddings
        industries = ", ".join(_as_list(c.get("industries")))
        recap = (
            f" This lesson emphasizes preventing recurrence via clear stakeholder alignment, "
            f"early risk surfacing, and explicit definitions of done. Applicable to "
            f"{industries or 'multiple industries'} during {c.get('phase') or 'project phases'}."
        )
        text = (text + recap).strip()

    today = date.today().isoformat()
    first = meta.get("first_validated") or today

    # Pull delivery model from client_profile when available
    delivery_model = (
        c.get("incident", {})
         .get("context", {})
         .get("client_profile", {})
         .get("delivery_model", meta.get("delivery_model", ""))
    )

    # Mirror schema-required subset into rag.meta
    new_meta = {
        "phase": c.get("phase", ""),
        "area": c.get("area", ""),
        "industries": _as_list(c.get("industries")),
        "severity": c.get("severity", ""),
        "tags": _as_list(c.get("tags")),
        "first_validated": first,
        "last_validated": today,
        # helpful (optional) extras:
        "project_size": meta.get("project_size", "M"),
        "team_composition": meta.get("team_composition", ""),
        "delivery_model": delivery_model,
    }

    c["rag"] = {"text": text, "meta": new_meta}
    return c

# --- sidecar writer ---
def _write_rag_sidecar(json_path: Path, text: str):
    sidecar = json_path.with_suffix(".rag")
    with open(sidecar, "w", encoding="utf-8") as f:
        f.write(text)

# --- minimal embedder + FAISS index ---
class Embedder:
    def __init__(self, model: str):
        self.model_name = model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError("Please install sentence-transformers")
        self.model = SentenceTransformer(model)

    def embed(self, texts: List[str]):
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

def build_faiss_index(vectors, out_dir: Path):
    try:
        import faiss
    except ImportError:
        raise RuntimeError("Please install faiss-cpu")
    import numpy as np
    vecs = vectors.astype("float32")
    d = vecs.shape[1]
    index = faiss.IndexFlatIP(d)
    # normalize for cosine
    faiss.normalize_L2(vecs)
    index.add(vecs)
    faiss.write_index(index, str(out_dir / "index.faiss"))

# --- commands ---
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
            print(f"❌ {p}\n{msg}\n")
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

    schema = DEFAULT_SCHEMA if not args.schema else load_json(Path(args.schema))
    files = iter_json_files(data_dir)
    if not files:
        print(f"No JSON files found under {data_dir}")
        return 1

    # load, ENSURE RAG (so TPMs never need to author it), validate, collect texts
    texts = []
    ids = []
    titles = []
    paths = []

    for p in files:
        doc = load_json(p)

        # 1) Build/refresh the rag block before validating
        doc = ensure_rag(doc, force=getattr(args, "force_autogen", False))

        # 2) Optionally write back the enriched JSON so source stays consistent
        if getattr(args, "write_back", False):
            try:
                with open(p, "w", encoding="utf-8") as wf:
                    json.dump(doc, wf, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️  Failed to write-back {p}: {e}")

        # 3) Validate after rag is present
        ok, msg = validate_json(doc, schema)
        if not ok:
            if args.strict:
                print(f"❌ {p} failed validation (strict mode).")
                print(msg)
                return 2
            else:
                print(f"⚠️  {p} failed validation; continuing (non-strict).\n{msg}\n")

        # write .rag sidecar next to the lesson JSON
        _write_rag_sidecar(p, doc["rag"]["text"])

        # normalized record for JSONL
        rec = {
            "id": doc["id"],
            "path": str(p),
            "title": doc["title"],
            "phase": doc["phase"],
            "area": doc["area"],
            "industries": doc["industries"],
            "severity": doc["severity"],
            "tags": doc["tags"],
            "rag_text": doc["rag"]["text"]
        }
        append_jsonl(chunks_path, rec)
        append_jsonl(ids_path, {"id": doc["id"], "path": str(p), "title": doc["title"]})
        texts.append(doc["rag"]["text"])
        ids.append(doc["id"])
        titles.append(doc["title"])
        paths.append(str(p))

    # embed & build FAISS
    embedder = Embedder(model=args.model)
    vecs = embedder.embed(texts)
    build_faiss_index(vecs, out_dir)

    # save metadata
    meta = {
        "created_at": datetime.now(UTC).isoformat(),
        "num_items": len(texts),
        "embedder": "sbert",
        "model": args.model,
    }
    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"✅ Built store at {out_dir} with {len(texts)} items.")
    return 0

def cmd_query(args):
    import numpy as np
    try:
        import faiss
    except ImportError:
        raise RuntimeError("Please install faiss-cpu")

    store = Path(args.store)
    index_path = store / "index.faiss"
    ids_path = store / "ids.jsonl"
    chunks_path = store / "chunks.jsonl"
    if not index_path.exists():
        raise RuntimeError(f"Missing index at {index_path}. Run build-index first.")

    # load ids + titles + paths
    ids: List[str] = []
    titles: List[str] = []
    paths: List[str] = []
    with open(ids_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ids.append(rec["id"])
            titles.append(rec["title"])
            paths.append(rec["path"])

    # embed query
    embedder = Embedder(model=args.model)
    xq = embedder.embed([args.q]).astype("float32")
    faiss.normalize_L2(xq)

    # search
    index = faiss.read_index(str(index_path))
    D, I = index.search(xq, args.k)
    print(f"\nTop {args.k} results for: {args.q}\n")
    for rank, (dist, idx) in enumerate(zip(D[0], I[0]), start=1):
        if idx == -1:
            continue
        print(f"{rank}. {titles[idx]}  (score={float(dist):.4f})")
        print(f"   id: {ids[idx]}")
        print(f"   file: {paths[idx]}\n")

def main():
    p = argparse.ArgumentParser(description="Antifragile Lessons RAG POC")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate JSON files against the schema")
    v.add_argument("--data", required=True, help="Directory with *.json lesson files")
    v.add_argument("--schema", help="Path to a schema file (optional; default: embedded)")
    v.set_defaults(func=cmd_validate)

    b = sub.add_parser("build-index", help="Build FAISS index from JSON files")
    b.add_argument("--data", required=True, help="Directory with *.json lesson files")
    b.add_argument("--out", required=True, help="Output directory for store")
    b.add_argument("--schema", help="Path to a schema file (optional; default: embedded)")
    b.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model (SBERT)")
    b.add_argument("--strict", action="store_true", help="Fail on first validation error")
    b.add_argument("--force-autogen", action="store_true", help="Always regenerate rag from canonical fields.")
    b.add_argument("--write-back", action="store_true", help="Persist auto-generated rag into the source JSONs.")
    b.add_argument("--reset", action="store_true", help="Reset (delete + rebuild) the output folder before building index")
    b.set_defaults(func=cmd_build_index)

    q = sub.add_parser("query", help="Query the store with a natural-language prompt")
    q.add_argument("--store", required=True, help="Path to store directory created by build-index")
    q.add_argument("--q", required=True, help="Natural language query")
    q.add_argument("-k", type=int, default=5, help="Top-k results")
    q.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
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
