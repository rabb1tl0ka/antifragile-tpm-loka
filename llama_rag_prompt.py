#!/usr/bin/env python3
import subprocess, json, shlex, textwrap, sys, shutil, textwrap, threading, queue, time, re


# --- CONFIG ---
RAG_SCRIPT = "./rag-ultralight.py"
STORE = "./rag_store_ultralight"
LLAMA_BIN = "../llama.cpp/build/bin/llama-cli"
MODEL = "../ai-llmacpp/models/llama/meta-llama-3.1-8b-instruct-q5_k_m.gguf"
TOP_K = 5

def run_rag(query: str, k: int = TOP_K):
    """Run rag-ultralight.py query and return parsed JSON results"""
    cmd = (
        f"python3 {shlex.quote(RAG_SCRIPT)} query "
        f"--store {shlex.quote(STORE)} "
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
            f"❌ {do_not}\n"
            f"✅ {do_yes}"
        )
    return "\n\n".join(blocks)

def query_llama(system_msg: str, 
                user_msg: str,
                llama_bin: str = LLAMA_BIN,
                model_path: str = MODEL,
                n_predict: int = 512,
                timeout_sec: int = 300) -> str:
    """
    Calls llama.cpp and returns ONLY the generated text as a Python string.
    Works with builds that don't support -ins/--system.
    """

    if not shutil.which(llama_bin):
        raise FileNotFoundError(f"llama binary not found: {llama_bin}")
    
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
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE,
        stderr=sys.stderr,           # <- stream logs live
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
    if len(sys.argv) < 2:
        user_q = input("Enter your question: ").strip()
    else:
        user_q = " ".join(sys.argv[1:])

    # 1) run RAG
    try:
        print(f"Querying RAG with query: {user_q}")
        rag = run_rag(user_q, TOP_K)
        results = rag.get("results", [])

        if not results:
            print("⚠️ No RAG results found.")
            return
    except:
        print("❌ RAG. Something went wrong.")
        return
    print("✅ RAG successful")

    # 2) build context
    print("Building context...")
    try:
        context = build_context(results)
        print(context)
    except:
        print("❌ Context. Something went wrong.")
        return
    
    print("✅ Building context successful")

    # 3) final system prompt
    system_msg = (
        "You are an experienced Technical Project Manager coach. "
        "When answering, speak directly to the user as if mentoring them in real-time. "
        "Balance empathy and authority: acknowledge challenges, then guide with practical next steps. "
        "Be concise but conversational, like a trusted advisor. "
        "Do not quote the question or lessons; instead, translate them into coaching advice."
        "Your mission is to help users avoid the mistakes that others have done and guide them back to robust alternatives."
        "Here's the lessons, each has 'Do NOT' and 'Do instead': {context}"
        "Use the lessons of what NOT to do in your answer."
        "Do not give more than 5 key points."
        
    )

    user_msg = f"Answer this question: {user_q}"

    # 4) query llama.cpp
    try:
        print("Querying llama.cpp ...")
        answer = query_llama(system_msg, user_msg)
        answer = clean_answer(answer)
        print(f"✅ LLM Answer: {answer}")
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return

if __name__ == "__main__":
    main()
