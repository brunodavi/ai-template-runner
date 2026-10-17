[provider]
base_url = 'http://localhost:8080/v1/chat/completions'
model = 'lfm230m'
[cmd]
message = 'echo hello'
+++
Read the output command: {cmd.message}

Answer the following question concisely: {question}
