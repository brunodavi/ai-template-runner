```toml
extends = 'base.md'

[provider]
temperature = 0
max_tokens = 80

[provider.extras]
response_format = { type = "json_object" }
```

---
Write a short email subject line (max 8 words) summarizing the message.

Return a JSON object with one key: `subject`.
Use the same language as the message.
Return only JSON.

Example:
{{"subject": "Rescheduling Installation Appointment"}}
---

Message:
{question}
