```toml
extends = '../base.md'

[provider]
temperature = 0.2
max_tokens = 120

[cmd]
message = 'echo hello'
```

---
You are a concise assistant. Use the command output as context when answering.
Do not repeat the instructions. Answer the user's question directly.
---

Command output:
{cmd.message}

Question: {question}
