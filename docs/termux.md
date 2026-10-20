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
pkg install python
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

Termux ships llama.cpp itself, so there is nothing to compile.

### The phone-safe server profile

Without explicit flags, `llama-server` inherits the model's native context
size (some models expose 32k) and spawns one thread per core — both will freeze
a phone. This is the safe daily profile on this project's reference device:

```sh
llama-server \
  --hf unsloth/Qwen3-0.6B-GGUF \
  --reasoning off \
  -c 2048 \
  -t 4 -tb 4 \
  -b 512 -ub 128 \
  -np 1 \
  --host 127.0.0.1 \
  --port 8080
```

| Flag | Why it is here |
|---|---|
| `--reasoning off` | reasoning/thinking tokens burn context and time; small models ramble in them |
| `-c 2048` | fixes the context window instead of trusting the model's native one (which can be 8–32k and melt the phone through KV cache RAM) |
| `-t 4 -tb 4` | generation and prompt-processing threads capped to 4 — the safe ceiling found here; start lower (1–2) on weaker phones |
| `-b 512 -ub 128` | batch shapes that smooth memory peaks during prompt processing |
| `-np 1` | one parallel slot — `ait` sends one request at a time anyway |
| `--host 127.0.0.1` | binds the server to the phone itself; unauthenticated API never reaches the network |
| `--port 8080` | matches the `base_url` in the template's `[provider]` config |

**About `-c`:** the template system is designed to keep prompts small
(`{cmd.*}` injection + slot-shaped user prompt), so 2048 covers prompt +
`max_tokens` answer comfortably. If a template needs more context, raise it to
4096 or 8192 **gradually, one step per run** — depending on the model it can
boost peak RAM use enough to freeze the whole device. Never assume a larger
context is free: the KV cache grows with it.

If your phone is stronger than the reference device, raise `--threads` first
(cheapest gain, less RAM), then `-c` — one knob at a time, watching whether the
UI stays fluid and the device stays cool. Thermal throttling eats the gains:
if the CPU ramps down mid-prompt, your effective speed is *lower* with more
threads.

The models this tool targets are small (0.3B–2B). Inference of a ~300-token
answer on the profile above stays in the seconds range — see the reference
numbers in [`docs/benchmarks.md`](benchmarks.md).

To run the built-in hardware benchmark, check that the package ships the tool:

```sh
command -v llama-bench
```

If it is there, follow the [`llama-bench` recipe](benchmarks.md#the-hardware-benchmark-built-into-llamacpp).
If the packager skipped that binary, the standard source build (below)
produces it at `build/bin/llama-bench`.

### Alternative installs

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
./build/bin/llama-server \
  --hf unsloth/Qwen3-0.6B-GGUF \
  --reasoning off -c 2048 -t 4 -tb 4 -b 512 -ub 128 -np 1 \
  --host 127.0.0.1 --port 8080
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
- Pin the model as a local file (`--model path/to/model.gguf` instead of
  `--hf`) when the network is not available.
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
