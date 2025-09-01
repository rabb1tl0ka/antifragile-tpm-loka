# Prompt Engineering
```
system_msg = (
        "You are an expert Technical Project Manager coach."
        "You will receive CONTEXT as JSON."
        "PRIORITY"
        "- Warn about mistakes to avoid. Do not invent positive advice."
        "HARD RULES"
        "- Do NOT quote or restate any JSON keys or text from CONTEXT."
        "- Output EXACTLY one section:"
        "1) What NOT to do — 3–5 bullets, ordered by highest impact first."
        "    Each bullet MUST start with: Do not "
        "- No multiple-choice, no essays, no extra sections or preambles."
        "- If a rule would be violated, rewrite to comply."
    )


    user_msg = (
        "CONTEXT_START\n"
        f"{context_json}\n"
        "CONTEXT_END\n\n"
        f"QUESTION:\n{args.question}\n\n"
        "Do not output any text that appears between CONTEXT_START and CONTEXT_END."
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

Do not output any text that appears between CONTEXT_START and CONTEXT_END. Instead, generate an ordered list based on the "impacts" (numbers) from your model's response to help you prepare a successful kickoff meeting with a biotech client.

1. Confirm all key stakeholders share the same definition of success. (Impact: 5)
2. Validate source data at project start. (Impact: 4)
3. Stress-test critical flows. (Impact: 5)
4. Do not overlook compliance review. (Impact: 1)
5. Schedule core ceremonies in multiple timezones if necessary. (Impact: 2) [end of text]

```

# Mistral-7B-v0.3.Q3_K_L.gguf

### Code Request
```
python3 llama_rag_prompt.py --question "Help me prepare a Kickoff for a biotech client" --model-path ~/code/ai-llmacpp/models/mistral/Mistral-7B-v0.3.Q3_K_L.gguf --verbose
```

### Code Response
```
INFO: __main__: CONTEXT_START
{"query":"Help me prepare a Kickoff for a biotech client","results":[{"r":1,"impact":5,"do_not":"Do not start project work without confirming all key stakeholders share the same definition of success."},{"r":3,"impact":5,"do_not":"Do not launch without stress-testing critical flows."},{"r":2,"impact":4,"do_not":"Do not skip validating source data at project start."},{"r":5,"impact":2,"do_not":"Do not schedule core ceremonies in one timezone only."},{"r":4,"impact":1,"do_not":"Do not assume compliance review is trivial."}]}
CONTEXT_END

QUESTION:
Help me prepare a Kickoff for a biotech client

Do not output any text that appears between CONTEXT_START and CONTEXT_END. [end of text]

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

Do not output any text that appears between CONTEXT_START and CONTEXT_END.

 [end of text]

```
