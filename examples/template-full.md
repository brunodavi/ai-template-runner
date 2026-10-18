```toml
[provider]
base_url = 'http://localhost:8080/v1/chat/completions'
model = 'lfm230m'

temperature = 0.2
top_p = 0.9
top_k = 40

min_p = 0.05
max_tokens = 220

seed = 42
stop = []

frequency_penalty = 0.0
presence_penalty = 0.0
repeat_penalty = 1.1

[provider.extras]
typical_p = 1.0
repeat_last_n = 64
mirostat = 0
mirostat_tau = 5.0
mirostat_eta = 0.1
```

Answer the following question clearly and concisely.

Question: {question}
