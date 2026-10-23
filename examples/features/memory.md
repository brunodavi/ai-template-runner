```toml
extends = '../base.md'

[memory]
base_url = 'http://localhost:8081/v1/embeddings'
model = 'nomic-embed-text'
source = 'memory-notes.txt'
db = 'memory.db'
chunk_size = 120
chunk_overlap = 10

[memory.notes]
```

---
You are a concise assistant. Ground every answer in the notes.
---

Relevant notes:
{memory.notes}

Answer the following question using only the notes: {question}
