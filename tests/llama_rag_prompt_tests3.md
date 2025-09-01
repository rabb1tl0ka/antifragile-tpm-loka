# Prompt Engineering

```
   system_msg = (
        "You are an expert Technical Project Manager coach.\n"
        "TASK: Produce exactly one section: 'What NOT to do'.\n"
        "OUTPUT FORMAT:\n"
        "- Write 3–5 bullet points.\n"
        "- Each bullet MUST start with: Do not \n"
        "- Order bullets by highest impact first.\n"
        "HARD RULES:\n"
        "- Use the CONTEXT only for reasoning; never copy or quote it.\n"
        "- No preamble, no title, no numbering, no explanations, no examples.\n"
        "- No 'what to do', no positive advice, no extra sections.\n"
        "QUALITY CHECK:\n"
        "- Before finalizing, rewrite any bullet that does not start with 'Do not '.\n"
        "- Remove any wording that prescribes actions to do.\n"
    )

    user_msg = (
        "CONTEXT_START\n"
        f"{context_json}\n"
        "CONTEXT_END\n\n"
        f"QUESTION:\n{args.question}\n\n"
        "Use the CONTEXT only to identify mistakes to avoid.\n"
        "Never copy text from between CONTEXT_START and CONTEXT_END.\n"
        "Respond with 3–5 bullet points, each starting with 'Do not '.\n"
       "Output ONLY the bullets.\n"
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

Use the CONTEXT only to identify mistakes to avoid.
Never copy text from between CONTEXT_START and CONTEXT_END.
Respond with 3–5 bullet points, each starting with 'Do not '.
Output ONLY the bullets.

Answers:
["Do not start project work without confirming all key stakeholders share the same definition of success.", "Do not launch without stress-testing critical flows.", "Do not skip validating source data at project start.", "Do not schedule core ceremonies in one timezone only.", "Do not assume compliance review is trivial."] [end of text]
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

Use the CONTEXT only to identify mistakes to avoid.
Never copy text from between CONTEXT_START and CONTEXT_END.
Respond with 3–5 bullet points, each starting with 'Do not '.
Output ONLY the bullets.

Answers:
["Do not start project work without confirming all key stakeholders share the same definition of success.", "Do not launch without stress-testing critical flows.", "Do not skip validating source data at project start.", "Do not schedule core ceremonies in one timezone only.", "Do not assume compliance review is trivial."] [end of text]
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

Use the CONTEXT only to identify mistakes to avoid.
Never copy text from between CONTEXT_START and CONTEXT_END.
Respond with 3–5 bullet points, each starting with 'Do not '.
Output ONLY the bullets. Do NOT include any other information (e.g., headers).

 [end of text]
```
