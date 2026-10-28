---
license: mit
library_name: peft
pipeline_tag: text-generation
language:
- en
base_model:
- Qwen/Qwen3.5-9B
- nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16
- Qwen/Qwen3-8B
base_model_relation: adapter
datasets:
- 9eve5h/rls-bench
tags:
- lora
- row-level-security
- postgres
- supabase
- sql
- grpo
- tinker
---

# RLS-Bench adapters

LoRA adapters trained on [RLS-Bench](https://github.com/devesh16145/rls-bench), a verifiable benchmark for Supabase/Postgres Row Level Security policies, with the benchmark's test harness as the training signal. The task set is at [9eve5h/rls-bench](https://huggingface.co/datasets/9eve5h/rls-bench).

Each folder is a standard PEFT adapter (`adapter_config.json`, `adapter_model.safetensors`) exported from [Tinker](https://thinkingmachines.ai/tinker/), with a `manifest.json` naming the Tinker run and checkpoint and giving the size and SHA-256 of `adapter_model.safetensors` as exported. The same manifests are committed in the GitHub repo as `results/train/adapter_manifest_*.json`, so a downloaded weights file can be checked against them. (The manifest's entry for `adapter_config.json` describes the file as Tinker wrote it; the export script then filled in the base model name, so that one file is a few bytes longer than recorded.)

Every number on this page is produced by code in that repo and stored under its `results/` directory. The full account, including the runs that did not work, is the repo's `docs/writeup.md` §5.

## What is here

<!-- adapter-table -->

Pass and leak rates are over 120 samples on the 20 held-out test tasks (6 per task: 5 at temperature 0.7 and one greedy), with 95% Wilson intervals on the pass rate. A **leak** is a test in which a simulated user saw or changed rows it should not have. Each row was evaluated on the test split once, pre-registered in the repo's `docs/preregistration.md` and locked to a commit; checkpoints were chosen on the 11 dev tasks.

<!-- judge-line -->

## What held up, and what did not

A tuned SFT is most of the gain for Qwen3.5-9B (9% → 38% pass). GRPO's dev gain did not transfer to test for Qwen (38% → 38–41%), and its two seeds disagree on the leak rate by 15 points, so at this scale run-to-run variance is as large as the effect. For Nemotron, GRPO cut the leak rate on 13 of 20 test tasks (31% → 10%), the one significant paired result. The highest pass rate of any row is the version-3 GRPO seed 0 (45%), at a higher leak rate than the version-2 SFT. The version-5 run at half batch made its SFT worse on every measure and is kept here as the negative result it is. The most reliable lever was not training at all: feeding the failing tests back took the GRPO model from 35% to 63% pass within three tries (`results/repair_eval/`, `results/test_eval_v2/*repair3*`).

## Training details

<!-- training-table -->

**SFT**: rank-32 LoRA on all linear layers, linear decay, loss on the answer only; the learning rate was chosen by a three-point sweep on held-out dev loss and that run is the model (nothing retrained). **GRPO**: the Tinker cookbook RL loop with group-centred rewards (8 answers per task at temperature 1.0), constant-reward groups dropped, the importance-sampling loss, no KL penalty. The harness is the reward: 1 for a pass, 0 for a safe failure (a block, or SQL that fails to apply), −0.1 for a format error and **−0.5 for a leak**, so a group that all fail still prefers failing closed. **Repair**: the same loop with up to three turns; after a failing try the model gets the names of the failing tests, the rules they cover, whether each was a leak or a block, and the SQL error, never the expected rows. **Distillation**: the cookbook's on-policy distillation from Qwen3.5-397B-A17B with the reward scaled to zero.

Prompt format: the fixed benchmark prompt (`eval/prompts.py` in the repo) in the base model's chat template with thinking disabled; the Tinker renderers were `qwen3_5_disable_thinking`, `nemotron3_ultra_disable_thinking` and, for the judge, `qwen3_disable_thinking`.

## How to load one

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = "Qwen/Qwen3.5-9B"
tokenizer = AutoTokenizer.from_pretrained(base)
model = AutoModelForCausalLM.from_pretrained(base, dtype="auto", device_map="auto")
model = PeftModel.from_pretrained(model, "9eve5h/rls-bench-adapters", subfolder="grpo_v3_Qwen3.5-9B_step40")
```

Use `base = "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16"` for the two Nemotron folders and `"Qwen/Qwen3-8B"` for the judge. To grade an answer, clone the repo and run `uv run rls run tasks/T001-* answer.sql`.

## Caveats

- The test split is 20 tasks: every interval above is wide, and most rows are within noise of each other.
- These are research artifacts from a small budget, not a policy generator for production use. The best adapter here still leaks on a quarter of its test samples.
- The base models' own licenses apply to anything built on them: Apache 2.0 for Qwen3.5-9B and Qwen3-8B, the NVIDIA Open Model License for Nemotron-3.5-Lightning.

## License

MIT, as the repo. The adapter weights are derived from the base models named above and the task set is CC-BY-4.0.
