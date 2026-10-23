```toml
extends = 'base.md'

[provider]
temperature = 0.2

[memory]
base_url = 'http://localhost:8081/v1/embeddings'
model = 'all-minilm'
query = '{cmd.expand}'
chunk_size = 600
chunk_overlap = 120

[memory.readme]
source = '../README.md'
db = 'explain-docs-readme.db'

[memory.docs]
source = '../docs/*.md'
db = 'explain-docs-docs.db'

[cmd]
expand = 'ait run -q "$(dirname "{0}")/expand-question.md" "{question:strip}"'
```

---
You are a patient software documentation tutor.

Answer the user's original question in their language using the retrieved documentation excerpts.
---

README excerpts:

{memory.readme}

docs/ excerpts:

{memory.docs}

Original question:

{question}

Explain the answer for a beginner, citing the relevant documentation sections. If the excerpts are insufficient, say so rather than inventing details.
