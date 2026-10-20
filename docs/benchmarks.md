# Reference capacity benchmark (small models)

A personal, non-official benchmark of small llama.cpp models, run on this
project's reference device (Samsung Galaxy M62, CPU only, one run per test) on
2026-10-20. Treat it as *behavioral reference*, not as an official benchmark:
model builds, llama.cpp version and prompt set are all single-run snapshots.

**Score = accuracy (up to 80) + speed per test (up to 20)** over 22 tests in 8
categories (logic, patterns, instruction following, robustness, abstention,
classification, extraction, JSON).

## Ranking

| Position | Model | Score | Accuracy | Latency/test | tok/s |
|---:|---|---:|---:|---:|---:|
| 1 | gemmaE2B.gguf | 78.3 | 95.5% | 6.82s | 1.5 |
| 2 | granite.gguf | 57.0 | 68.2% | 5.39s | 1.7 |
| 3 | qwen8m.gguf | 46.3 | 50.0% | 2.08s | 3.9 |
| 4 | grok4-1b-q4_km.gguf | 46.0 | 54.5% | 5.47s | 1.6 |
| 5 | gemma3-1b-q5.gguf | 43.9 | 50.0% | 3.37s | 3.8 |
| 6 | gemma3-1b-it-qat-q4.gguf | 41.4 | 45.5% | 2.61s | 4.0 |
| 7 | lfm350m.gguf | 35.5 | 27.3% | 0.95s | 7.7 |
| 8 | lfm230m.gguf | 34.5 | 18.2% | 0.65s | 17.9 |

## What this means for template design

The numbers confirm the premise this tool is built on — **small models fail
not because they are slow, but because they lose structure** — and they show
directly which models reproduce on which template shape:

- **Speed is not correctness.** The fastest model (lfm230m, 17.9 tok/s) scores
  lowest on accuracy and failed every JSON test, while the slowest (~1.5 tok/s)
  scored 95.5%. If your workflow includes `[test]`, the fastest model often
  costs *more* time per accepted answer.
- **Structured output survives better than reasoning.** `JSON` and
  `Extraction` categories score well across models (even 350m/230m hit 100% on
  some extraction tests), while `Logic` collapses below 1B parameters. Slot
  templates with JSON answers are the strong use; open-ended deduction is the
  weak use.
- **A 2B-class model rates a real harness.** gemmaE2B passed 95.5% including
  logic and robustness — validating every upgrade a category — and shows this
  class is viable on a phone when the template keeps the model on-task.
- **`[test]` turns "dumb model" silence into signal.** Abstention tests
  ("does it admit not knowing?") are where most models broke;
  a `[test]` on an abstention marker makes that failure visible per run.

## Full per-category matrix

Categories: Abstention, Classification, Extraction, Instruction, JSON, Logic,
Patterns, Robustness (accuracy per model, %):

| Category | gemmaE2B | granite | qwen8m | grok4-1b | gemma3-1b-q5 | gemma3-1b-qat | lfm350m | lfm230m |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Abstention | 100 | 0 | 50 | 50 | 0 | 0 | 50 | 50 |
| Classification | 100 | 50 | 100 | 50 | 50 | 50 | 50 | 0 |
| Extraction | 100 | 100 | 50 | 100 | 50 | 50 | 50 | 100 |
| Instruction | 80 | 40 | 40 | 60 | 20 | 20 | 20 | 0 |
| JSON | 100 | 100 | 100 | 75 | 75 | 75 | 50 | 0 |
| Logic | 100 | 50 | 0 | 0 | 50 | 0 | 0 | 0 |
| Patterns | 100 | 100 | 33 | 66 | 100 | 100 | 0 | 0 |
| Robustness | 100 | 100 | 0 | 0 | 50 | 50 | 0 | 50 |

Latency and accuracy trade-off (accuracy vs latency/test):

| Model | Score | Latency/test | Accuracy |
|---|---:|---:|---:|
| gemmaE2B.gguf | 78.3 | 6.82s | 95.5% |
| granite.gguf | 57.0 | 5.39s | 68.2% |
| qwen8m.gguf | 46.3 | 2.08s | 50.0% |
| lfm350m.gguf | 35.5 | 0.95s | 27.3% |
| lfm230m.gguf | 34.5 | 0.65s | 18.2% |

## Real model identities (from the llama.cpp build tags)

The file names above are the working labels; llama.cpp identified them as:

| File | Actual model | Size | Params |
|---|---|---:|---:|
| lfm230m.gguf | lfm2 230M Q4_K - Medium | 144 MiB | 230M |
| lfm350m.gguf | lfm2 350M Q4_K - Medium | 216 MiB | 354M |
| qwen8m.gguf | qwen3.5 0.8B Q4_K - Medium | 494 MiB | 752M |
| grok4-1b-q4_km.gguf | *granite 2B* Q4_K - Medium (not Grok) | 973 MiB | 1.63B |
| granite.gguf | granitehybrid 1B Q4_K - Medium | 856 MiB | 1.46B |
| gemma3-1b-it-qat-q4.gguf | gemma3 1B Q4_0 (QAT) | 681 MiB | 1.0B |
| gemma3-1b-q5.gguf | gemma3 1B Q5_0 | 764 MiB | 1.0B |
| gemmaE2B.gguf | gemma4 E2B Q4_K - Medium (MoE) | 2.88 GiB | 4.65B |

## Hardware curve — reference phone, CPU-only (llama-bench)

Ran with the [phone-safe profile](termux.md#the-phone-safe-server-profile) on
the same reference device (`llama-bench -p 512 -n 128 -t 1,2,4 -r 3 --delay 5`),
covering every model in the behavioral ranking above.

pp512 / tg128, tokens per second, at 1 / 2 / 4 threads:

| File | pp512 t1 | pp512 t4 | tg128 t1 | tg128 t2 | tg128 t4 |
|---|---:|---:|---:|---:|---:|
| lfm230m | 22.00 | 95.65 | 12.73 | 22.91 | **45.53** |
| lfm350m | 12.50 | 53.01 | 8.54 | 15.71 | 29.25 |
| gemma3-1b-qat | 11.66 | 29.35 | 4.05 | 6.76 | 12.50 |
| qwen8m | 7.52 | 32.48 | 2.62 | 10.65 | 11.57 |
| gemma3-1b-q5 | 7.23 | 23.87 | 3.21 | 6.16 | 9.32 |
| granite | 3.97 | 14.85 | 1.51 | 5.87 | 8.33 |
| grok4-1b (granite 2B) | 3.19 | 10.69 | 1.92 | 3.68 | 7.17 |
| gemmaE2B | 3.61 | 9.01 | 1.50 | 3.84 | 3.81 |

What the curves say, cross-referenced with the behavioral scores:

- **Scaling is near-linear up to 4 threads only under ~2B params.** lfm230m
  tg128 goes 12.7 → 45.5 t/s (3.6×) across 1 → 4 threads. But gemmaE2B
  saturates at 2 threads (3.84 → 3.81 t/s): the 2.9 GiB MoE gains *nothing*
  from the extra cores on this device — for the accuracy champion, 2 threads
  is already the ceiling.
- **Quantization costs real speed on CPU.** Same 1B gemma3 model: Q4_0 does
  12.50 t/s at 4 threads, Q5_0 does 9.32 — ~25% slower for the extra accuracy
  retention.
- **The speed/accuracy Pareto holds on hardware.** lfm350m (29.25 t/s, among
  the fastest) with only 27.3% accuracy is the "many quick [test]-filtered
  retries" pick; gemmaE2B (3.8 t/s but 95.5% accuracy) is the "few,
  expensive, usually-correct runs" pick. granite sits between: 8.33 t/s for
  68.2% accuracy.
- **End-to-end vs raw:** the behavioral benchmark's end-to-end tok/s (which
  includes tokenization, sampling, prompt processing and app overhead) reads
  ~2.5–4× below the `llama-bench` tg numbers for the same model (e.g. lfm230m:
  17.9 end-to-end vs 45.5 raw). Use the raw curve for capacity planning and
  the behavioral tok/s for what a user will actually feel per `ait run`.

## The hardware benchmark built into llama.cpp

The section above (`Hardware curve`) was produced with llama.cpp's own
hardware benchmark, `llama-bench`, which measures raw speed — how fast this
device, CPU-only, burns prompts and tokens. To reproduce or add another
device's curve:

```sh
llama-bench -m model.gguf -p 512 -n 128 -t 1,2,4 -r 3
```

- `-p 512 -n 128`: how many prompt tokens to process (`pp` test) and how many
  tokens to generate (`tg` test);
- `-t 1,2,4`: runs the sweep below and above the phone-safe
  [`--threads` profile](termux.md#the-phone-safe-server-profile) in one go,
  so you can see exactly where the phone stops paying off (scaling usually
  flattens first, then regresses when the SoC throttles);
- `-r 3`: repeats per test, averaged (5 is the default; 3 keeps the run
  shorter on battery);
- `--delay 5` (optional, seconds): cooldown between tests, kind to phones;
- `-o csv` / `-o json` (optional): machine-friendly output for a spreadsheet
  or a git-tracked results file.

The run pegs the CPU for its whole duration — close apps, let the phone cool,
and keep other background inference off while it runs. Note that these measurements exclude tokenization and sampling, so the
t/s here will read a bit above the tok/s in the behavioral ranking (which
measures end-to-end).

Two values matter for template tuning:

- **`pp t/s` (prompt processing)** — how expensive your `{cmd.*}` context
  injection is; large injected outputs cost you here;
- **`tg t/s` (text generation)** — the real speed of the answer; this is what
  determines how long `[test]`-budgeted templates take per run.

If you benchmark your own phone, record `model`, threads (`-t`), context, the
`pp`/`tg` numbers and the llama.cpp build (`llama-bench` prints it), and open
a PR — behavioral scores from `docs/benchmarks.md` + hardware curves together
make the capacity map much more useful than either alone.
