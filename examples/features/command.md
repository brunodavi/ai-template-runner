```toml
extends = '../base.md'

[cmd]
message = 'echo hello'
slot = 'echo {question} interpolated'
```

Read the output commands: {cmd.message} and {cmd.slot}

Answer the following question concisely: {question}
