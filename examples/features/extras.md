```toml
[provider]
base_url = "http://localhost:8080/v1/chat/completions"
model = "lfm230m"

[provider.extras]
repeat_last_n = 64
typical_p = 0.95
mirostat = 0
```

Answer the following question in one short sentence.

Question: {question}
