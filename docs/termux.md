# Running ai-template-runner on a phone with Termux

This is the environment where the tool was born: a mid-range Android phone
(tested on a Samsung Galaxy M62), Termux, llama.cpp serving a small GGUF model
locally, and `ait` wrapping that server into structured, validated workflows.

Everything here is a community guide — paths and package names change between
Termux versions. If a step fails, prefer what Termux prints.

## 1. Termux + uv

Install [F-Droid](https://f-droid.org) and then the Termux app (the Play Store
build is outdated). Inside Termux:

```sh
pkg update
pkg install uv python build-essential
```

`uv` gives you the CLI with one command:

```sh
uvx ai-template-runner --help
```

For a persistent install:

```sh
uv tool install ai-template-runner
ait --help
```

If `uv` is unavailable in your Termux mirror, install it the standard way:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. llama.cpp with a small model

```sh
pkg install git cmake clang make
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build -j$(nproc)
```

Pull and serve a small GGUF model — the class of models this tool is built
around (0.5B–2B parameters respond in seconds on a phone):

```sh
./build/bin/llama-server -hf unsloth/Qwen3-0.6B-GGUF --port 8080
```

Leave that server running in one Termux session and open another one for
`ait`. Every tool that speaks the OpenAI chat protocol on `localhost` works the
same way (Ollama and LM Studio can also run inside a proot Linux distribution —
that is how this project itself is developed: Termux with an Alpine proot
underneath it).

## 3. Point templates at the phone server

`ait` works entirely offline against the local server:

```sh
ait run examples/email-subject.md "my boss canceled the launch tomorrow" --quiet
```

Because the small model that answers is the weakest link, let the template do
the structural work already:

- keep the user prompt a slotted, repetitive shape — small models are far more
  reliable filling a fixed template than improvising a workflow;
- use `{cmd.*}` to inject real command output as context instead of trusting
  the model to know your system;
- use `[test]` so a hallucinated answer becomes a visible FAIL instead of a
  silent wrong result;
- use `[out]` to format JSON answers into one-line output that is safe to pipe.

## 4. Practical knobs

- `max_tokens` in the `[provider]` table keeps phone-sized responses fast.
- `temperature = 0.2` and `[provider.extras]` with llama.cpp options like
  `repeat_last_n` stabilize small models noticeably.
- Battery/network: `llama-server` converts on demand; pin the model files with
  `hf pull` if you serve the same model repeatedly.
- For long sessions, run Termux under `termux-wake-lock` so Android does not
  pause the server.

## Known limits

- Termux's Python is *fast enough* for template processing, not for
  model-serving. Keep inference in llama.cpp.
- Some Termux mirrors lag behind Python 3.13/3.14; `ai-template-runner`
  requires Python 3.12+, which any current Termux Python satisfies.
- If you publish your phone's server beyond `localhost`, remember
  llama.cpp's API is unauthenticated — keep it on-device or behind a tunnel
  you control.
