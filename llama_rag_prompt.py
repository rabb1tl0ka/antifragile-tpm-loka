#!/usr/bin/env python3
import subprocess
import json
import shlex
import textwrap
import sys
import shutil
import textwrap
import re
import argparse
from pathlib import Path
import logging
from typing import Any, Dict, List, Union, Optional

log = logging.getLogger(__name__)

def run_rag(query: str, rag_script: str, rag_store: str, k: int):
    """Run rag-ultralight.py query and return parsed JSON results"""
    cmd = (
        f"python3 {shlex.quote(rag_script)} query "
        f"--store {shlex.quote(rag_store)} "
        f"--q {shlex.quote(query)} "
        f"-k {k} "
        f"--json-response"
    )
    raw = subprocess.check_output(cmd, shell=True, text=True)
    log.debug("RAG raw output: %s", raw)
    data = json.loads(raw)

    if not isinstance(data, dict):
        raise TypeError(
        "rag-ultralight.py --json-response must return a JSON object with keys 'query' and 'results', "
        f"but got {type(data).__name__}. Raw snippet: {raw[:240]}…"
        )
    if "results" not in data or not isinstance(data["results"], list):
        raise KeyError(
        "Invalid RAG JSON: missing 'results' list. Expected {\"query\": str, \"results\": [ ... ]}. "
        f"Keys present: {list(data.keys())}"
        )
    if "query" not in data:
        log.warning("RAG JSON missing 'query' field; proceeding with empty string.")
        data["query"] = query
    
    return data

def build_context(results: list, max_len: int = 200) -> str:
    blocks = []
    for r in results:
        do_not = r["guidance"]["do_not_do"].strip()
        do_yes = r["guidance"]["do_instead"].strip()
        if len(do_not) > max_len: do_not = do_not[:max_len-1] + "…"
        if len(do_yes) > max_len: do_yes = do_yes[:max_len-1] + "…"
        blocks.append(
            f"[{r['rank']}] {r['title']} (impact {r['impact']})\n"
            f"DO NOT: {do_not}\n"
            f"DO: {do_yes}"
        )
    return "\n\n".join(blocks)

def to_compact_context(
    rag: Dict[str, Any],
    *,
    include_titles: bool = True,
    max_items: Optional[int] = None,
    min_impact: int = 0,
    sort_by: str = "impact_desc_rank_asc",
) -> Dict[str, Any]:
    """
    Convert *stable* RAG output (object) into a compact CONTEXT payload.

    Requires shape: {"query": str, "results": [ {...}, ... ]}
    Keeps only: rank (r), impact, optional title, do_not, do_instead
    """
    if not isinstance(rag, dict) or "results" not in rag or not isinstance(rag["results"], list):
        raise ValueError(
            "to_compact_context expects an object with a 'results' list. "
            f"Got: {type(rag).__name__} with keys {list(rag.keys()) if isinstance(rag, dict) else 'N/A'}"
        )

    query = rag.get("query", "")
    results = rag["results"]

    def norm_item(r: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(r, dict):
            return None
        impact = int(r.get("impact", 0) or 0)
        if impact < min_impact:
            return None
        g = r.get("guidance", {}) or {}
        do_not = g.get("do_not_do") or g.get("do_not") or ""
        do_instead = g.get("do_instead") or ""
        item = {
            "r": int(r.get("rank", 0) or 0),
            "impact": impact,
            "do_not": str(do_not).strip(),
            #"do_instead": str(do_instead).strip(), #  <- we're hiding the do_instead to not influence the 
            #model
        }
        if include_titles and "title" in r:
            item["title"] = str(r["title"]).strip()
        return item

    items: List[Dict[str, Any]] = []
    for r in results:
        ni = norm_item(r)
        if ni:
            items.append(ni)

    if sort_by == "impact_desc_rank_asc":
        items.sort(key=lambda x: (-x["impact"], x["r"]))
    elif sort_by == "rank_asc":
        items.sort(key=lambda x: x["r"])  # leave as-is otherwise

    if max_items is not None:
        items = items[:max_items]

    return {"query": query, "results": items}


def dumps_compact(obj: Any) -> str:
    """Stable, compact JSON for prompts (saves tokens)."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def query_llama(system_msg: str, 
                user_msg: str,
                llama_bin: str,
                model_path: str,
                n_predict: int = 512,
                timeout_sec: int = 300) -> str:
    """
    Calls llama.cpp and returns ONLY the generated text as a Python string.
    Works with builds that don't support -ins/--system.
    """

    if not shutil.which(llama_bin):
        raise FileNotFoundError(f"llama binary not found: {llama_bin}")
    
    if not Path(model_path).is_file():
        raise FileNotFoundError(f"model file not found: {model_path}")
    
     # Clean whitespace
    system_msg = textwrap.dedent(system_msg).strip()
    user_msg   = textwrap.dedent(user_msg).strip()

    cmd = [
        llama_bin,
        "-m", model_path,
        "-t", "12", "--threads-batch", "12",
        "--ctx-size", "4096",
        "--temp", "0.2", "--top-p", "0.95",
        "--repeat-penalty", "1.25", "--repeat-last-n", "320",
        "--n-predict", str(n_predict),
        "-no-cnv",
        "--system-prompt", system_msg,
        "--prompt", user_msg,
    ]

    cmd.extend([
        "--stop", "CONTEXT_START",
        "--stop", "CONTEXT_END",
        "--stop", "QUESTION:",
        "--stop", "Answer:",
        "--stop", "Answers:",
    ])


    # Capture stdout+stderr; llama.cpp prints loader info to stderr
    if log.isEnabledFor(logging.DEBUG):
        _stderr = sys.stderr
    else:
        _stderr = subprocess.DEVNULL

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=_stderr,
        text=True,
        bufsize=1,
    )
    out, err = proc.communicate(timeout=timeout_sec)

    if proc.returncode != 0:
        raise RuntimeError(f"llama.cpp exited with code {proc.returncode}\n{err}")

    return out.strip()

def clean_answer(ans: str) -> str:
    # remove special tokens if any slipped through
    for tok in ("<|eot_id|>", "<|end_of_text|>"):
        ans = ans.replace(tok, "")
    ans = ans.strip()

    # If it starts by echoing the question/lessons, drop that preamble.
    # Heuristic: find the first of our requested sections and cut before it.
    m = re.search(r"(?m)^\s*1\)\s*Top 3 risks to avoid", ans)
    if m:
        ans = ans[m.start():].lstrip()

    # If the model wrote our bullet headers with bold/markdown numbers,
    # accept variants too:
    if not m:
        m2 = re.search(r"(?im)^(?:top\s*3\s*risks|\*\*top\s*3\s*risks)", ans)
        if m2:
            ans = ans[m2.start():].lstrip()

    return ans

def main():

    parser = argparse.ArgumentParser(description="Run RAG + Llama pipeline")

    parser.add_argument(
        "--rag-script",
        default="./rag-ultralight.py",
        help="Path to RAG script (default: ./rag-ultralight.py)"
    )
    parser.add_argument(
        "--store",
        default="./rag_store_ultralight",
        help="Path to RAG store (default: ./rag_store_ultralight)"
    )
    parser.add_argument(
        "--llama-bin",
        default="../llama.cpp/build/bin/llama-cli",
        help="Path to llama.cpp binary (default: ../llama.cpp/build/bin/llama-cli)"
    )
    parser.add_argument(
        "--model-path",
        default="../ai-llmacpp/models/llama/meta-llama-3.1-8b-instruct-q5_k_m.gguf",
        help="Path to model file (default: ../ai-llmacpp/models/llama/meta-llama-3.1-8b-instruct-q5_k_m.gguf)"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Top k results to get from RAG"
    )
    parser.add_argument(
        "-q", "--q", "--question",
        dest="question",
        required=True,
        help="The question you want to ask"
    )
    parser.add_argument("-v", "--verbose", 
        action="store_true",
        help="See debug and troubleshooting information")
    
    parser.add_argument("--no-titles", 
        action="store_true", 
        default=True,
        help="Do not include lesson titles in CONTEXT")

    args = parser.parse_args()
    
    # Configure logging based on --verbose
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(name)s: %(message)s"
    )

    log.debug("CLI args: %s", vars(args))   # only prints when -v/--verbose is set

    # 1) RAG
    log.info("Querying RAG…")
    rag = run_rag(args.question, args.rag_script, args.store, args.k)
    results = rag.get("results", [])
    if not results:
        print("No RAG results found.")
        return

    # 2) Compact CONTEXT
    log.info("Building CONTEXT…")
    context_obj = to_compact_context(rag, include_titles=not args.no_titles)
    context_json = dumps_compact(context_obj)
    log.debug("CONTEXT JSON: %s", context_json)
    
    # 3) final system prompt

    system_msg = (
        "You are an expert Technical Project Manager coach.\n"
        "TASK: Produce exactly one section: 'What NOT to do'.\n"
        "OUTPUT FORMAT:\n"
        "- Write 3–5 bullet points.\n"
        "- Each bullet MUST start with: Do not \n"
        "- Order bullets by highest impact first.\n"
        "STYLE:\n"
        "- Phrase each bullet in natural coaching language.\n"
        "- Each bullet MUST include a brief consequence after an em dash (—), no period before the dash.\n"
        "- Keep it concrete (operations, timelines, data quality, compliance) but concise.\n"
        "HARD RULES:\n"
        "- Use the CONTEXT only for reasoning; never copy or quote it.\n"
        "- Output ONLY plain-text bullets (no JSON/arrays/quotes/headers/prefix hyphens or numbering).\n"
        "- Your FIRST character must be 'D' from 'Do not '.\n"
        "QUALITY CHECK:\n"
        "- If any bullet lacks an em dash consequence, add one.\n"
        "- If any line does not start with 'Do not ', rewrite it.\n"
    )

    user_msg = (
        "CONTEXT_START\n"
        f"{context_json}\n"
        "CONTEXT_END\n\n"
        f"QUESTION:\n{args.question}\n\n"
        "From the CONTEXT, output 3–5 plain-text bullets.\n"
        "Each MUST start with 'Do not ' and include an em dash (—) followed by a short consequence.\n"
        "Do not include any headings, labels, or leading hyphens. The first character must be 'D'.\n"
    )


    # 4) query llama.cpp
    print("Querying llama.cpp ...")
    answer = query_llama(system_msg, user_msg, args.llama_bin, args.model_path)
    answer = clean_answer(answer)
    log.info(answer)


if __name__ == "__main__":
    main()
