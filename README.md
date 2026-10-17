# AI Template Runner

AIT is a lightweight CLI for testing local AI models and creating simple, reusable AI workflows with Markdown templates.

Templates combine **TOML configuration** and prompt instructions in a single file, separated by `+++`. The configuration is TOML, not YAML.

## Installation

Install directly from GitHub using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/brunodavi/ai-template-runner.git
```

## Usage

Run a template with an optional question:

```bash
ait run examples/template-full.md "What is Python?"
```

See available commands:

```bash
ait --help
```

## Templates

Example templates are available in [`examples/`](examples/).

```markdown
base_url = 'http://localhost:8080/v1/chat/completions'
model = 'lfm230m'
+++
Answer the following question concisely:
{question}
```

The TOML section configures the provider and model. The prompt body supports the `{question}` placeholder, replaced with the question supplied through the CLI.

## Development

Clone the repository and install it in editable mode using `uv`:

```bash
git clone https://github.com/brunodavi/ai-template-runner.git
cd ai-template-runner
uv sync
uv pip install -e .
```

Editable installation lets you run `ait` directly while developing. Changes to the Python source are available without reinstalling the package each time.

Test your changes with:

```bash
ait run examples/template-full.md "What is Python?"
```

## Status

AIT is an early-stage project focused on simple local AI experimentation and lightweight workflows.
