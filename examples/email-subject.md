```toml
[provider]
base_url = 'http://localhost:8080/v1/chat/completions'
model = 'lfm230m'

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
