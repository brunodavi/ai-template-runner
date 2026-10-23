# AI Template Runner

Small local models are cheap and fast — they also lose structure the moment a prompt gets long. `ait` turns that weakness into a workflow: each template is a single Markdown file that gathers context, prompts the model, validates the answer and renders the result. Deterministic scaffolding around a dumb-but-fast model, even one running on your phone.

A template is one file with a TOML section (model, endpoint, sampling), an optional system prompt, the user prompt (with `{cmd.*}` command output and `{question}` input slots), and optional `[test]` / `[out]` tables to validate and render the answer.

One file, one command, one predictable answer — no agent framework needed.

**Why it matters:** a small model cannot keep a workflow in its head, but it can fill in a well-shaped slot. Templates put the workflow in the file so the model only has to do the part it is good at. Failures become visible and reproducible through `[test]`, instead of vague "the model is dumb" sessions.

## Quick start

Point `ait` at any OpenAI-compatible chat endpoint (llama.cpp server, Ollama, LM Studio, ...):

1. Start a model server, e.g. llama.cpp:

```bash
llama-server -hf unsloth/Qwen3-0.6B-GGUF --port 8080
```

2. Run a ready template:

```bash
uvx ai-template-runner run TEMPLATE "What is Python?"
```

Or clone the repository and try it against a fixture without a model at
all — the `examples/simulation/` templates run against fixed
responses, so you can feel the `[test]`/`[out]` mechanics in seconds:

```bash
git clone https://github.com/brunodavi/ai-template-runner.git
cd ai-template-runner
uvx ai-template-runner run examples/simulation/conventional-commits/feat.md --test
```

Running on a phone? See [`docs/termux.md`](docs/termux.md).

## Installation

| Command | When to use |
| --- | --- |
| `uvx ai-template-runner --help` | zero-install trial from [PyPI](https://pypi.org/project/ai-template-runner/) |
| `pipx install ai-template-runner` | persistent install, any platform (Termux ships pipx) |
| `pip install ai-template-runner` | any pip environment |
| `uv tool install ai-template-runner` | [uv](https://docs.astral.sh/uv/) managed installs |
| `uv tool install git+https://github.com/brunodavi/ai-template-runner.git` | latest `master` |

Requires Python 3.12+. The CLI is `ait` (or `ai-template-runner`); the package has **zero runtime dependencies**.

## Usage

```bash
ait run examples/features/full.md "What is Python?"
ait run examples/features/full.md "What is Python?" --quiet
ait run examples/simulation/conventional-commits/feat.md --test
ait run "examples/features/*.md"                      # batch: quoted glob runs every template
ait run examples/features/args.md first second        # positional args fill {1}, {2}...
ait run examples/features/args.md -- "-not-a-flag"    # everything after -- is verbatim arg data
ait --help
ait run --help
```

- `-q` / `--quiet`: display only the AI response (stdout stays clean for pipes).
- `-t` / `--test`: validate the response against the template's `[test]` table. PASS/FAIL lines go to stderr and the exit code is 1 when any check fails.
- `--fail-fast`: with a batch and `--test`, stop at the first template with a FAIL.

The template argument is always resolved the same way: an existing file is used directly (absolute or relative), and anything else is matched as a glob pattern relative to the current directory (`**` recursion works). A batch runs every match in sorted order; files that do not start with the ` ```toml ` configuration block are skipped with a warning on stderr. One resolved file that is not a template is a usage error.

## Templates

Templates combine **TOML configuration** and Markdown prompts in a single file. The configuration is defined in a ` ```toml ` code block at the beginning of the file, and is parsed and removed from the prompt content. Two ` --- ` separators delimit an optional system prompt; everything after them becomes the user prompt. Templates can also execute terminal commands and inject their output directly into prompts.

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

`{question}` is the alias of `{1}`: with `run TEMPLATE "My Question"`, both render the first value after the template. Positional slots:

| Placeholder | Value |
|---|---|
| `{0}` | absolute path of the running template (for a batch, each run gets its own path) |
| `{1}` / `{question}` | first value after the template |
| `{2}`, `{3}`, ... | subsequent values |

`{0}` and every positional value are `Smart` strings, so pythonic slices and inline transforms work on them the same way they do inside `[out]`: `{0[1:]}`, `{question:strip}`, `{2[:8]}`, `{2:replace:old:new}`. The `{cmd.message}` placeholder executes the configured command and inserts its output into the prompt. Placeholders can be used in both the system and user prompts.

The `[cmd]` values themselves also interpolate the run slots — interpolation is lazy (the slots fill in right before the subprocess runs, when the placeholder is evaluated) and raw, nothing quotes for you, so what reaches the shell is exactly what you word it:

```toml
[cmd]
context = 'grep "{question}" notes.txt'
logs = 'tail -n 20 {0[1:]} 2>&1 | head -50'
```

- The value supports positional slots, slices and transforms (`grep "{1}"`, `ls {0[1:]}`, `echo {question:strip}`) — same semantics as the prompts, with usage errors naming `[cmd] <name>` (`unknown placeholder ...`, `not enough args in [cmd] ...`).
- Literal shell braces must be doubled (`awk '{{print $2}}'`): config values go through `str.format` like prompts.
- Nothing quotes the interpolation for you — if the args come from someone else's command line, treat the value as shell code under their control and quote your command parts deliberately.

The provider supports these generation parameters:

- `temperature`, `top_p`, `top_k`, `min_p`: control sampling.
- `max_tokens`: limits the generated response length.
- `seed`: sets the random seed when supported.
- `stop`: defines stop sequences.
- `frequency_penalty`, `presence_penalty`, `repeat_penalty`: control repetition.
- `extras`: passes additional parameters to the API, such as llama.cpp-specific options.

`base_url` and `model` are required. Parameter support depends on the API and model server being used.

A template can ground its answers in local notes with a `[memory]` table. It declares an embeddings
endpoint (like `[provider]`) plus one named collection per `[memory.<name>]` table; each collection
becomes a retrieval slot through the `{memory.<name>}` placeholders — lazy like `{cmd.*}`: the
retrieval runs only when the placeholder is actually interpolated, and once per run:

```toml
[memory]
base_url = 'http://localhost:8081/v1/embeddings'   # full endpoint URL, like [provider]
model = 'nomic-embed-text'
source = 'notes/notes.md'     # data file: literal path or glob, relative to the template file
db = 'notes/memory.db'        # sqlite index; omitted, one is created next to the first source
query = '{question}'          # default question for the collections (placeholders allowed)

chunk_size = 1024             # maximum characters per chunk
chunk_overlap = 128           # stride of shared characters between sliding windows
batch_size = 16               # texts per /v1/embeddings request
top_k = 4                     # chunks returned per retrieval
max_chars = 2048              # injected context budget
min_score = 0.0               # minimum relevance filter; 0 keeps it predictable

[memory.extras]               # extra payload for the endpoint, like [provider.extras]

[memory.notes]                # collection: an empty table inherits every [memory] setting
```

```markdown
---
Use the notes as ground truth.
---
Notes:
{memory.notes}

Answer the following question: {question}
```

How the retrieval works:

- The notes are chunked preserving paragraphs: paragraphs that fit share one chunk (joined by a
  newline), oversized ones are cut by a sliding window whose stride is
  `chunk_size - chunk_overlap`.
- The index is a local sqlite3 file gated by a fingerprint (sha256 of the sources plus the
  chunking/model parameters). `ait run` itself rebuilds the index when the notes or the
  parameters change — no separate update command needed.
- The collection `query` interpolates the same slots as the prompts (`{question}`, `{0}`,
  `{1}...`) before embedding, and the result places like a `Smart` value: `{memory.notes:strip}`
  and `{memory.notes[:500]}` work like any other placeholder.
- `[memory.<name>]` tables participate in `extends` inheritance like every other config table.
- Point `base_url` at any OpenAI-compatible `/v1/embeddings` endpoint (llama.cpp server,
  Ollama, LM Studio, ...). See [`examples/features/memory.md`](examples/features/memory.md).

Chunk behavior in practice, measured with real notes and a MiniLM-class
embedding model (single-run evidence, phone CPU):

- **The chunk is the ranking item.** With a generous `chunk_size`, paragraphs pack whole into
  one chunk (joined by a newline) and retrieval injects fewer, cohesive pieces. Lowering
  `chunk_size` below the paragraph length switches those notes to sliding windows instead —
  the stride overlap then injects the characters around every cut, and the seams are visible
  in the prompt (`... the release workflow ` ending one chunk, `and write a matching ...`
  starting the next).
- **Seams can cost answer quality.** In a model swap test over the same notes, a chunk size
  smaller than the paragraphs made a strong 8B chat model see the same sentence three times
  and emit a duplicated step in its answer, while the packed configuration produced a clean,
  complete answer. Keep `chunk_size` above your paragraphs' length when the notes are short
  paragraphs; use small chunks deliberately when you want note-level granularity.
- **On a short-window embedding model** (MiniLM-class, ~256-token context), `chunk_size` in
  the 200–600 chars range keeps each chunk inside the embedding window without truncation.
- **Retrieval is a selection pipeline:** up to `top_k` chunks (default 4) past the
  `min_score` filter, capped by `max_chars` — with fewer than `top_k` candidates inside the
  budget, `{memory.notes}` simply carries what fits. The first ranked chunk always enters.
- **A `min_score` set above the conversation's hit level renders `{memory.notes}` empty** —
  off-topic questions produced an empty context and the chat model answered without notes.
  Keep `min_score = 0.0` (default) unless you intentionally want the quality gate.
- **Retuning retrieval knobs never re-embeds.** `top_k`, `min_score` and `max_chars` are
  outside the index fingerprint: change them freely between runs. Editing the notes, the
  chunking parameters or the embeddings model is what triggers a rebuild.

A template can inherit configuration, commands, and prompts from another template with a top-level `extends` key placed before any TOML table:

```toml
extends = 'base.md'

[provider]
temperature = 0.2
```

The `extends` path is resolved relative to the template file itself, so [`examples/features/`](examples/features/) templates use `extends = '../base.md'`. Child values win per key; nested tables such as `[provider.extras]` and `[cmd]` are merged key by key. Empty child prompts fall back to the parent prompts, which lets a template reuse only the parent prompts and configuration.

A template can validate its own output with a `[test]` table and the `--test` flag:

```toml
[test]
type = 'feat'                              # JSON output field equality
message = 'add health check endpoint'      # exact value comparison
"user.name" = 'Alice'                      # nested JSON path (quoted dotted key)

text = 'exact raw output'                  # exact raw text comparison
text_contains = ['GET_health']             # every fragment present in the raw text
text_regex = '^\{'                         # regex search on the raw text
```

Run with validation:

```bash
ait run examples/simulation/conventional-commits/feat.md --test
ait run "examples/**/*.md" --test    # batch: aggregated exit code over every template
```

PASS/FAIL lines go to stderr (stdout stays clean for pipes) and the exit code is 1 when any check fails. Missing JSON fields and invalid JSON output fail instead of raising. The `[test]` table participates in `extends` inheritance like the other config tables.

A template can also render its own display output with an `[out]` table. The `text` key is a render template formatted with the parsed JSON fields (`{out.type}`, `{out.message}`, ...); missing fields render as empty:

```toml
[out]
text = '{out.type}: {out.message}'
```

Transforms run in two channels that never share the field namespace (`out.count` is always the JSON field, never `str.count`):

```toml
[out]
text = '{out.message:strip} | {out.message:replace:GET:SET} | {out.message[:4]}'

[[out.upper]]                               # one step: str.upper() with no args

[[out.replace]]                             # named args match the real str signature
old = 'GET_health'
new = 'GET'

[[out.slice]]                               # helper: builtin slice(start, end)
start = 1
end = 10
```

The `[[out.<method>]]` tables run in real document order (one table = one step, an empty table means no arguments) and apply to the rendered `text` — or to the raw response when there is no `text`. Steps are real `str` methods, with named arguments mapped positionally by the real signature. The inline spec is a single step from `method:arg1:arg2` (argument values may not contain ':'), and `{out.field[1:]}` follows pythonic slice syntax. Without `[out]` (or an empty table) the raw AI response is printed. The `[out]` config participates in `extends` inheritance per key: the child `text` and step lists replace the parent's.

The same inline transforms work on every interpolated value in the prompts — `{question:strip}`, `{question[:80]:lower}`, `{0[1:]}` and `{cmd.message:upper}`, `{cmd.status[1:20]}` — since the value stays lazy for `{cmd.*}` (the command only runs when a field is actually used). See [`examples/features/args.md`](examples/features/args.md) for the positional placeholders in action.

## Examples and docs

See [`examples/base.md`](examples/base.md) for the shared base used by the examples, [`examples/features/`](examples/features/) for one example per feature, [`examples/`](examples/) for ready-to-use task templates such as [`email-subject.md`](examples/email-subject.md) and [`conventional-commits.md`](examples/conventional-commits.md), and [`examples/simulation/`](examples/simulation/) for simulations that run task templates against fixed fixtures.

For deeper material, read [`docs/architecture.md`](docs/architecture.md) (why the code is
shaped the way it is), [`docs/termux.md`](docs/termux.md) (running local models on a phone),
[`docs/benchmarks.md`](docs/benchmarks.md) (what small models can and cannot do)
and [`docs/maintenance.md`](docs/maintenance.md) (release routine for maintainers).

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
ait run examples/features/full.md "What is Python?"
```

Run the test suite (from the repository root):

```bash
uv run python -m unittest
```

Contributions are welcome — CI runs the suite on Python 3.12, 3.13 and 3.14, so that is the floor.

## Status

AIT is in active development for local AI experimentation and lightweight, template-driven workflows. Expect the template syntax to be stable and everything around it to keep evolving. See [`CHANGELOG.md`](CHANGELOG.md) for release history.

Licensed under the [MIT license](LICENSE).
