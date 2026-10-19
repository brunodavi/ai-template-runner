```toml
[provider]
base_url = 'http://localhost:8080/v1/chat/completions'
model = 'gemma3-1b-q5'

temperature = 0

[provider.extras]
response_format = { type = "json_object" }

[cmd]
status = "git status"
staged = "git diff --cached"
unstaged = "git diff"
```

---
Generate a Conventional Commit type and message based on the Git status, diffs, and untracked file paths provided. Use the available information to understand the changes without assuming behavior that is not shown. Choose one type from `feat`, `fix`, `docs`, `style`, `refactor`, `test`, or `chore`. Write a short, imperative commit message in English, without the type prefix. Return only a valid JSON object containing exactly the keys `type` and `message`.

Example:
```json
{{
  "type": "docs",
  "message": "add installation instructions to README"
}}
```
---

Git status:
{cmd.status}

Staged diff:
{cmd.staged}

Unstaged diff:
{cmd.unstaged}
