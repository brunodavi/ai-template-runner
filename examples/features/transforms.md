```toml
extends = '../base.md'

[out]
text = '{out.type}: {out.message:strip}'

[[out.replace]]
old = 'GET_health'
new = 'GET'

[[out.upper]]
```

The question is passed without its surrounding spaces: {question:strip}

Return a JSON object with:
- `type`: the commit type of the request
- `message`: the commit message, mentioning GET_health when needed

Return only JSON.

Question: {question}
