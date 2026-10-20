# Running ai-template-runner on a phone with Termux

This is the environment where the tool was born: a mid-range Android phone
(tested on a Samsung Galaxy M62), Termux, llama.cpp serving a small GGUF model
locally, and `ait` wrapping that server into structured, validated workflows.

Terminal output varies between Termux versions; when a command drifts from
what your terminal prints, prefer what your terminal tells you.

## 1. Install the CLI directly with Python

The package is a pure-Python wheel on [PyPI](https://pypi.org/project/ai-template-runner/)
with zero runtime dependencies — no compiler, no toolchain:

```sh
pkg update
pkg install python python-pip
pip install ai-template-runner
ait --help
```

That is the whole CLI install. If you already use [uv](https://docs.astral.sh/uv/),
it replaces the step above:

```sh
uvx ai-template-runner --help          # zero-install trial
uv tool install ai-template-runner     # persistent install
```

## 2. llama.cpp straight from the Termux packages

Termux ships llama.cpp itself, so there is nothing to compile:

```sh
pkg install llama-cpp
llama-server --hf unsloth/Qwen3-0.6B-GGUF --port 8080
```

`pkg search llama` also lists:

- `llama-cpp` — CPU backend, installs and runs with no extra setup;
- `llama-cpp-backend-opencl` / `llama-cpp-backend-vulkan` — optional GPU
  backends. On this project's test device (M62) both failed so far, most
  likely because of the device's Vulkan/OpenCL driver API level — the CPU
  backend is the safe default;
- `ollama` (+ `ollama-backend-vulkan`) — alternative model server; anything
  speaking the OpenAI chat protocol on `localhost` works with `ait`, since
  llama.cpp's server itself exposes that-compatible endpoints.

If the packager ever drops the package, build from source as a fallback:

```sh
pkg install git cmake clang make
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build && cmake --build build -j$(nproc)
./build/bin/llama-server --hf unsloth/Qwen3-0.6B-GGUF --port 8080
```

Leave the server running in one Termux session and use `ait` in another.

Pull small GGUF models (0.5B–2B parameters) — this is the class of model the
templates are shaped around, and they answer within seconds on a phone.

## 3. Point templates at the phone server

`ait` works entirely offline against the local server:

```sh
ait run examples/email-subject.md "my boss canceled the launch tomorrow" --quiet
```

Feel the mechanics without any model at all by cloning the repo — the
`examples/simulation/` templates run against fixed responses:

```sh
git clone https://github.com/brunodavi/ai-template-runner.git
cd ai-template-runner
ait run examples/simulation/conventional-commits/feat.md --test
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
- Converting/park the same model as a file (`--model path/to/file.gguf`)
  instead of `--hf` when the network is not available.
- For long sessions, run Termux under `termux-wake-lock` so Android does not
  pause the server.

## Known limits

- Termux's Python is fast enough for template processing, not for
  model-serving. Keep inference in llama.cpp.
- Some Termux mirrors lag behind on Python version; `ai-template-runner`
  requires Python 3.12+, which a current Termux Python satisfies.
- The GPU backends (OpenCL/Vulkan) failed on this project's test device so far;
  the CPU backend is the baseline that works everywhere.
- If you publish your phone's server beyond `localhost`, remember llama.cpp's
  API is unauthenticated — keep it on-device or behind a tunnel you control.
