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
