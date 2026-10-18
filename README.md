# AI Template Runner

AIT is a lightweight CLI for testing local AI models and creating reusable AI workflows with Markdown templates.

Templates combine **TOML configuration** and prompt instructions in a single file, separated by `+++`. They can also execute terminal commands and inject their output directly into prompts.

## Installation

Install directly from GitHub using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/brunodavi/ai-template-runner.git
```

## Usage

```bash
ait run examples/template-full.md "What is Python?"
ait --help
```

## Templates

Templates use TOML for configuration and Markdown for prompts. The `provider` section requires `base_url` and `model`.

```markdown
[provider]
base_url = 'http://localhost:8080/v1/chat/completions'
model = 'lfm230m'

[cmd]
message = 'echo hello'
+++
Command output: {cmd.message}

Answer the following question concisely: {question}
```

The `{question}` placeholder is replaced with the CLI input. The `{cmd.message}` placeholder executes `echo hello` and inserts its output (`hello`) directly into the prompt.

See [`examples/`](examples/) for more templates.

## Development

```bash
git clone https://github.com/brunodavi/ai-template-runner.git
cd ai-template-runner
uv sync
uv pip install -e .
```

Editable mode lets you run `ait` directly while developing, with source changes available without reinstalling.

Test your changes:

```bash
ait run examples/template-full.md "What is Python?"
```

## Status

AIT is an early-stage project for local AI experimentation and lightweight, template-driven workflows.
