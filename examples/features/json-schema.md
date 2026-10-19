```toml
[provider]
base_url = 'http://localhost:8080/v1/chat/completions'
model = 'lfm230m'

temperature = 0

[provider.extras]
response_format = { type = "json_schema", json_schema = { name = "datetime_extraction", strict = true, schema = { type = "object", properties = { date = { type = ["string", "null"], description = "Date in YYYY-MM-DD format" }, time = { type = ["string", "null"], description = "Time in HH:MM format" } }, required = ["date", "time"], additionalProperties = false } } }

[cmd]
datetime = "date"
```

---
Extract the date and time from the input.

Rules:
- Do not invent missing values.
- Return only JSON.

Input: {cmd.datetime}
---

Get the date time for me
