# Prompt Engineering

```
    system_msg = (
        "You are an expert Technical Project Manager coach.\n"
        "TASK: Produce exactly one section: 'What NOT to do'.\n"
        "OUTPUT FORMAT:\n"
        "- Write 3–5 bullet points.\n"
        "- Each bullet MUST start with: Do not \n"
        "- Order bullets by highest impact first.\n"
        "STYLE:\n"
        "- Phrase each bullet in natural coaching language.\n"
        "- Each bullet MUST include a brief consequence (after an em dash: — ).\n"
        "HARD RULES:\n"
        "- Use the CONTEXT only for reasoning; never copy or quote it.\n"
        "- Output ONLY plain-text bullets (no JSON, no lists, no arrays, no quotes, no headers).\n"
        "- Your FIRST character must be 'D' from 'Do not '.\n"
        "QUALITY CHECK:\n"
        "- If any bullet lacks an em dash and consequence, add one before finalizing.\n"
    )

    user_msg = (
        "CONTEXT_START\n"
        f"{context_json}\n"
        "CONTEXT_END\n\n"
        f"QUESTION:\n{args.question}\n\n"
        "From the CONTEXT, extract 3–5 mistakes to avoid.\n"
        "Output ONLY plain-text bullets; each must start with 'Do not ' and include an em dash (—) with a short consequence.\n"
    )
```

# mistral-7b-instruct-v0.2.Q4_K_M.gguf

## Code
### Request
```
python3 llama_rag_prompt.py --question "Help me prepare a Kickoff for a biotech client" --model-path ~/code/ai-llmacpp/models/mistral/mistral-7b-instruct-v0.2.Q4_K_M.gguf --verbose
```

### Response
```
INFO: __main__: CONTEXT_START
{"query":"Help me prepare a Kickoff for a biotech client","results":[{"r":1,"impact":5,"do_not":"Do not start project work without confirming all key stakeholders share the same definition of success."},{"r":3,"impact":5,"do_not":"Do not launch without stress-testing critical flows."},{"r":2,"impact":4,"do_not":"Do not skip validating source data at project start."},{"r":5,"impact":2,"do_not":"Do not schedule core ceremonies in one timezone only."},{"r":4,"impact":1,"do_not":"Do not assume compliance review is trivial."}]}
CONTEXT_END

QUESTION:
Help me prepare a Kickoff for a biotech client

From the CONTEXT, extract 3–5 mistakes to avoid.
Output ONLY plain-text bullets; each must start with 'Do not ' and include an em dash (—) with a short consequence.

Answer:
- Do not start project work without confirming all key stakeholders share the same definition of success. — Misaligned expectations can lead to delays or suboptimal outcomes.
- Do not launch without stress-testing critical flows. — Failure to identify bottlenecks early on may result in unexpected issues during implementation.
- Do not skip validating source data at project start. — Inaccurate information could cause incorrect assumptions and impact downstream processes.
- Do not schedule core ceremonies in one timezone only. — Excluding team members from different locations might hinder collaboration and engagement.
- Do not assume compliance review is trivial. — Neglecting this step can result in costly rework due to noncompliance with regulations. [end of text]

```

# Mistral-7B-v0.3.Q3_K_L.gguf

### Code Request
```
python3 llama_rag_prompt.py --question "Help me prepare a Kickoff for a biotech client" --model-path ~/code/ai-llmacpp/models/mistral/Mistral-7B-v0.3.Q3_K_L.gguf --verbose
```

### Code Response
```
NFO: __main__: CONTEXT_START
{"query":"Help me prepare a Kickoff for a biotech client","results":[{"r":1,"impact":5,"do_not":"Do not start project work without confirming all key stakeholders share the same definition of success."},{"r":3,"impact":5,"do_not":"Do not launch without stress-testing critical flows."},{"r":2,"impact":4,"do_not":"Do not skip validating source data at project start."},{"r":5,"impact":2,"do_not":"Do not schedule core ceremonies in one timezone only."},{"r":4,"impact":1,"do_not":"Do not assume compliance review is trivial."}]}
CONTEXT_END

QUESTION:
Help me prepare a Kickoff for a biotech client

From the CONTEXT, extract 3–5 mistakes to avoid.
Output ONLY plain-text bullets; each must start with 'Do not ' and include an em dash (—) with a short consequence. [end of text]

```

# phi-2.Q4_K_M.gguf


### Code Request
```
python3 llama_rag_prompt.py --question "Help me prepare a Kickoff for a biotech client" --model-path ~/code/ai-llmacpp/models/phi3/phi-2.Q4_K_M.gguf  --verbose
```

### Code Response
```
INFO: __main__: CONTEXT_START
{"query":"Help me prepare a Kickoff for a biotech client","results":[{"r":1,"impact":5,"do_not":"Do not start project work without confirming all key stakeholders share the same definition of success."},{"r":3,"impact":5,"do_not":"Do not launch without stress-testing critical flows."},{"r":2,"impact":4,"do_not":"Do not skip validating source data at project start."},{"r":5,"impact":2,"do_not":"Do not schedule core ceremonies in one timezone only."},{"r":4,"impact":1,"do_not":"Do not assume compliance review is trivial."}]}
CONTEXT_END

QUESTION:
Help me prepare a Kickoff for a biotech client

From the CONTEXT, extract 3–5 mistakes to avoid.
Output ONLY plain-text bullets; each must start with 'Do not ' and include an em dash (—) with a short consequence.

 [end of text]
```
