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
    print(f"RAG raw output: {raw}")
    print("loading JSON from RAG raw output")
    return json.loads(raw)
    

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

    args = parser.parse_args()
    
    # Configure logging based on --verbose
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(name)s: %(message)s"
    )

    log.debug("CLI args: %s", vars(args))   # only prints when -v/--verbose is set

    # 1) run RAG
    try:
        print(f"Querying RAG with query: {args.question}")
        rag = run_rag(args.question, args.rag_script, args.store, args.k)
        results = rag.get("results", [])

        if not results:
            print("No RAG results found.")
            return
    except:
        print("Exception RAG. Something went wrong.")
        return
    print("RAG successful")

    # 2) build context
    print("Building context...")
    try:
        context = build_context(results)
        print(context)
    except:
        print("Exception Context. Something went wrong.")
        return
    
    print("Building context successful")

    # 3) final system prompt
    system_msg = (
        f"You are an experienced Technical Project Manager coach. "
        f"When answering, speak directly to the user as if mentoring them in real-time. "
        f"Balance empathy and authority: acknowledge challenges, then guide with practical next steps. "
        f"Be concise but conversational, like a trusted advisor. "
        f"Do not quote the question or lessons; instead, translate them into coaching advice."
        f"Your mission is to help users avoid errors and mistakes. You need to look up the lessons prefaced with DO NOT."
        f"Here's the lessons, each has 'Do NOT' and 'Do instead': {context}"
        f"Do not give more than 5 key points."
    )

    user_msg = f"Answer this question: {args.question}"

    # 4) query llama.cpp
    print("Querying llama.cpp ...")
    answer = query_llama(system_msg, user_msg, args.llama_bin, args.model_path)
    answer = clean_answer(answer)
    print(f"LLM Answer: {answer}")
    
if __name__ == "__main__":
    main()
