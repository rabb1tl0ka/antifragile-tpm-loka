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
```

# mistral-7b-instruct-v0.2.Q4_K_M.gguf

## Code
### Request
```
python3 llama_rag_prompt.py --question "Help me prepare a Kickoff for a biotech client" --model-path ~/code/ai-llmacpp/models/mistral/mistral-7b-instruct-v0.2.Q4_K_M.gguf --verbose
```

### Response
```

```

# Mistral-7B-v0.3.Q3_K_L.gguf

### Code Request
```
python3 llama_rag_prompt.py --question "Help me prepare a Kickoff for a biotech client" --model-path ~/code/ai-llmacpp/models/mistral/Mistral-7B-v0.3.Q3_K_L.gguf --verbose
```

### Code Response
```

```

# phi-2.Q4_K_M.gguf


### Code Request
```
python3 llama_rag_prompt.py --question "Help me prepare a Kickoff for a biotech client" --model-path ~/code/ai-llmacpp/models/phi3/phi-2.Q4_K_M.gguf  --verbose
```

### Code Response
```
```
