```toml
extends = '../base.md'

[provider]
temperature = 0

[provider.extras]
response_format = { type = "json_object" }

[cmd]
datetime = "date"
```

---
Extract the date and time from the input.

Return a JSON object with:
- `date`: date in `YYYY-MM-DD` format, or `null` if absent.
- `time`: time in `HH:MM` format, or `null` if absent.

Return only JSON.

Input: {cmd.datetime}

Example:
{{"date": "2026-10-25", "time": "14:30"}}
---

Get the date time for me
