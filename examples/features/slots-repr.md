```toml
extends = '../base.md'

[cmd]
word = 'echo {1:upper} -- {1!r}'
```

The question is wrapped in repr quotes: {question!r}

Custom style first, repr second: {cmd.word}

Plain just in case: {question}
