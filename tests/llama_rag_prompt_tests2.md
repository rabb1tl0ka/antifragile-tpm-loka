# Prompt Engineering
```

system_msg = (
    "You are an expert Technical Project Manager coach.\n"
    "You will receive CONTEXT as JSON.\n\n"
    "PRIORITY\n"
    "- Warn about mistakes to avoid. Do not invent positive advice.\n\n"
    "HARD RULES\n"
    "- Do NOT quote or restate any JSON keys or text from CONTEXT.\n"
    "- Output EXACTLY one section:\n"
    "  1) What NOT to do — 3–5 bullets, ordered by highest impact first.\n"
    "     Each bullet MUST start with: Do not ...\n"
    "- No multiple-choice, no essays, no extra sections or preambles.\n"
    "- If a rule would be violated, rewrite to comply.\n"
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

Do not output any text that appears between CONTEXT_START and CONTEXT_END. Here are some suggestions to help you prepare a successful kickoff meeting with your biotech client:

1. Confirm shared definitions of success (Impact 5): Before starting any project work, make sure all key stakeholders have a clear understanding of what constitutes success for this initiative. This includes both business objectives as well as technical goals. Use collaborative techniques like workshops or surveys to ensure alignment on these expectations.

2. Stress-test critical flows (Impact 5): Identify essential processes within the project scope and validate them thoroughly during the kickoff session. This will give everyone involved an opportunity to discuss potential challenges, identify dependencies, and establish mitigation strategies if necessary.

3. Validate source data at project start (Impact 4): Ensure accurate information by verifying the quality and completeness of input data before beginning the actual implementation phase. Involve relevant team members in this process to minimize errors later on.

4. Schedule core ceremonies across multiple timezones (Impact 1): If working with international teams or remote participants, consider scheduling Agile ceremonies flexibly so they can accommodate different time zones without causing undue burden on anyone.

5. Assume compliance review is non-trivial (Impact 2): Compliance requirements may add complexity to your project timeline and budget. Be prepared to allocate sufficient resources towards ensuring regulatory standards are met throughout the development lifecycle.

6. Prepare engaging presentations and activities (Impact 3): Keep attendees engaged by using visuals, interactive exercises, and real-life examples when presenting project details during the Kickoff event. Encourage active participation from all parties involved to foster collaboration and build momentum around the project vision. [end of text]

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
