```toml
extends = '../base.md'

[out]
text = '{out.type}: {out.message}'
```

Return a JSON object with:
- `type`: the commit type of the request below
- `message`: the commit message in imperative mood

Return only JSON.

Question: {question}
