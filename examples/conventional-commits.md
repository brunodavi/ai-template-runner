```toml
extends = 'base.md'

[provider]
model = 'qwen3-0.8b'
temperature = 0
max_tokens = 100

[provider.extras]
response_format = { type = "json_object" }

[cmd]
status = "git status"
staged = "git diff --cached"
unstaged = "git diff"
```

---
Classify the Git changes and generate a Conventional Commit message.

Type guide:
- feat: adds new behavior, endpoint, option or capability
- fix: repairs a bug or handles an error case
- docs: changes only Markdown or documentation content
- style: code formatting only (spaces, indentation), no behavior change
- refactor: neither fixes a bug nor adds a feature (renames, moves, cleanups)
- test: adds or changes tests only
- chore: build config, .gitignore, dependencies, tooling

Write a short, imperative commit message in English, without any prefix. Return only a JSON object with exactly the keys `type` and `message`.

Examples:
{{"type": "feat", "message": "add health check endpoint"}} -> for new endpoints or functions
{{"type": "fix", "message": "handle missing argument"}} -> for try/except or error handling
{{"type": "style", "message": "remove extra spaces"}} -> formatting only
---

Git status:
{cmd.status}

Staged diff:
{cmd.staged}

Unstaged diff:
{cmd.unstaged}
