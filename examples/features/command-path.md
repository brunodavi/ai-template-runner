```toml
extends = '../base.md'

[cmd]
head = 'head -n 2 "$(dirname "{0}")/command-context.txt"'
```

First lines of the sibling data file:

{cmd.head}

Answer the following question concisely: {question}
