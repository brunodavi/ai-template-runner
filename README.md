# AI Template Runner

AIT is a lightweight CLI for testing local AI models and creating reusable AI workflows with Markdown templates.

Templates combine **TOML configuration** and Markdown prompts in a single file. The configuration is defined in a ` ```toml ` code block at the beginning of the file, and is parsed and removed from the prompt content. Two ` --- ` separators delimit an optional system prompt; everything after them becomes the user prompt. Templates can also execute terminal commands and inject their output directly into prompts.

## Installation

Install directly from GitHub using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/brunodavi/ai-template-runner.git
```

## Usage

```bash
ait run examples/template-full.md "What is Python?"
ait run examples/template-full.md "What is Python?" --quiet
ait --help
ait run --help
```

Use `-q` or `--quiet` to display only the AI response.

## Templates

Templates use TOML for configuration and Markdown for prompts. The configuration is written in a ` ```toml ` code block at the beginning of the file. The `[provider]` section configures the API endpoint, model, and generation parameters.

````markdown
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

[cmd]
message = 'echo hello'
```

---
You are a concise assistant. Use the command output as context.
---

Command output:
{cmd.message}

Answer the following question concisely: {question}
````

The TOML block is parsed and removed from the prompt content. The optional system prompt is delimited by two `---` separators; everything after the second separator is the user prompt. When the separators are omitted, the whole content after the configuration block is the user prompt.

The `{question}` placeholder is replaced with the CLI input. The `{cmd.message}` placeholder executes the configured command and inserts its output into the prompt. Placeholders can be used in both the system and user prompts.

The provider supports these generation parameters:

- `temperature`, `top_p`, `top_k`, `min_p`: control sampling.
- `max_tokens`: limits the generated response length.
- `seed`: sets the random seed when supported.
- `stop`: defines stop sequences.
- `frequency_penalty`, `presence_penalty`, `repeat_penalty`: control repetition.
- `extras`: passes additional parameters to the API, such as llama.cpp-specific options.

`base_url` and `model` are required. Parameter support depends on the API and model server being used.

See [`examples/`](examples/) for more templates.

## Development

```bash
git clone https://github.com/brunodavi/ai-template-runner.git
cd ai-template-runner
uv sync
uv pip install -e .
```

Editable installation (`-e .`) lets you run `ait` directly while developing, so source changes are available without reinstalling.

Run a template to test your changes:

```bash
ait run examples/template-full.md "What is Python?"
```

Run the test suite:

```bash
python -m unittest
```

## Status

AIT is an early-stage project for local AI experimentation and lightweight, template-driven workflows.
