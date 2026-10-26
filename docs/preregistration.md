# Pre-registration: version 2 test evaluation

Written before the version 2 test evaluation ran. The checkpoints were filled in as each run finished and
the file was not edited after the evaluation started. The evaluation ran on 2026-10-26 at commit 54bb76a
(`results/test_eval_v2/LOCK.json`).

## What is evaluated

On the 20 test tasks, with the baseline protocol (1 greedy sample + 5 at temperature 0.7, 4,096-token
cap, reasoning-off template):

| Row | Model | How chosen |
|---|---|---|
| base | Qwen3.5-9B, untrained | — |
| sft | best SFT sweep run | lowest final dev loss (`results/train/sft_sweep_*.json`) |
| sft+rl | best GRPO checkpoint | highest dev pass rate over all 66 dev samples during the run |
| sft+rl, seed 2 / second student | as above | same rule |
| repair | best repair-RL checkpoint | highest dev pass-after-3-tries |

Chosen checkpoints (filled in before running):

| Row | Run | Checkpoint | Why |
|---|---|---|---|
| base | Qwen/Qwen3.5-9B | — | — |
| sft | 20261025T184758Z (sft_Qwen3.5-9B lr 4.73e-4) | final | lowest final dev loss of the three sweep runs (0.1413) |
| sft+rl | 20261025T191833Z (rl_Qwen3.5-9B_lr4e-5_s50) | step 40 | highest dev pass rate of the five evals (52%) |
| sft+rl, seed 2 | rl_Qwen3.5-9B_lr4e-5_s50_seed1 | step 40 | highest dev pass rate of the five evals (53%) |
| repair | 20261025T194632Z (repair_Qwen3.5-9B_from40_s25) | step 5 | highest dev pass after 3 tries of the five evals (67%) |
| base (Nemotron) | nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16 | — | — |
| sft (Nemotron) | 20261025T190749Z (sft lr 3e-4) | final | lowest final dev loss of the three sweep runs (0.153) |
| sft+rl (Nemotron) | 20261025T193419Z (rl_Nemotron_lr6e-5_s50) | step 50 (final) | highest dev pass rate of the five evals (38%) |
| distil | distil_Qwen3.5-9B_from397B_s40 | step 30 | highest dev pass rate of the four evals (29%) |

## Primary measures

1. Pass rate over all 120 test samples, with a 95% Wilson interval, per row.
2. Leak rate over all 120 test samples, per row.
3. Paired comparison by task (pass count out of 6, leak count out of 6) between consecutive rows, two-sided
   sign test.

## Secondary measures

Greedy pass@1 (n = 20), apply-error rate, format-error rate, mean answer length, pass and leak by tier, pass by
trap. For the repair row and the sft+rl row: pass rate after 1, 2 and 3 tries with harness feedback (the same
3-try protocol as on dev), run once alongside the single-answer protocol.

## What would count as a result

- A real improvement from RL: higher pass rate than the SFT row and no higher leak rate, with the paired
  comparison favouring RL on more tasks than it disfavours.
- Reward hacking signals, reported whichever way they come out: answers getting much shorter, tier 1
  improving while tiers 2–3 do not, greedy and sampled leak rates moving in opposite directions.

## Disclosure

The test split was evaluated once before, for version 1 (commit 1bc6904, 2026-10-25). No training decision
in version 2 used test results; checkpoints are chosen on dev only.

---

# Pre-registration: version 3 test evaluation

Written before the version 3 test evaluation runs; filled in as runs finish and not edited after the evaluation starts.

**What changes in version 3:** the SFT data. Version 2 trained on 427 DeepSeek-sampled answers; version 3 trains on 460 answers drawn round-robin from DeepSeek and Kimi K2.6 (`data/sft_v3.jsonl`, 72 references, 246 DeepSeek, 142 Kimi, `results/train/sft_v3_stats.json`). Everything else (SFT recipe and sweep, GRPO recipe and learning rate 4e-5, 50 steps × 16 tasks × 8 rollouts, two seeds, dev selection by highest dev pass rate) is held fixed from version 2 so that the comparison isolates the data.

| Row | Run | Checkpoint | Why |
|---|---|---|---|
| base | Qwen/Qwen3.5-9B | — | same as version 2 |
| sft v3 | sft_v3_Qwen3.5-9B_20261026T050548Z_lr0.00024 (lr 2.4e-4) | final | lowest final dev loss of the three sweep runs (0.1546) |
| sft v3 + GRPO, seed 0 | rl_v3_Qwen3.5-9B_lr4e-5_s40 (40 steps; stalled at 25 and resumed from the step-20 checkpoint) | step 40 | highest dev pass rate of the four saved-checkpoint evals (61%) |
| sft v3 + GRPO, seed 1 | rl_v3_Qwen3.5-9B_lr4e-5_s30_seed1 (30 steps, not 40: remaining credit) | step 20 | highest dev pass rate of the three evals (35%) |

**Measures:** as in version 2 (pass and leak over 120 test samples with Wilson intervals; paired sign tests by task against the version 2 rows `sft`, `sft+rl`, `sft+rl-seed1`, which are reused from `results/test_eval_v2/`, not re-run).

**What would count as a result:** version 3 SFT above version 2 SFT on test pass with no higher leak rate; and the GRPO-over-SFT comparison repeated with the new data, again reported whichever way it goes.

**Disclosure:** this is the third evaluation of the test split (version 1 at 1bc6904, version 2 at 54bb76a). No training decision used test results.

---

# Pre-registration: version 4 test evaluation (one row)

Written before it runs. **What changes:** ten newly verified tasks (T104–T113) were appended to the train split, Kimi K2.6 was sampled on them, and the version-3 SFT recipe was re-run at the same learning rate (2.4e-4) on the enlarged data (491 examples, 82 tasks). No GRPO follows (remaining credit).

| Row | Run | Checkpoint | Why |
|---|---|---|---|
| sft-82 | sft_v3b_Qwen3.5-9B_20261026T124124Z_lr0.00024 | final | the only run (single learning rate, no sweep) |

**Measures:** pass and leak over the 120 test samples with Wilson intervals; paired sign tests by task against `sft` (version 2, 72 tasks, DeepSeek data) and `sft-v3` (version 3, 72 tasks, two-source data), reused from their result files.

**What would count as a result:** a higher pass rate than `sft-v3` with no higher leak rate, which would attribute the dev gain to the extra train tasks rather than noise.

**Disclosure:** the fourth evaluation of the test split (versions 1–3 at 1bc6904, 54bb76a, 34bab1f). No training decision used test results.

---

# Pre-registration: version 5 test evaluation (one row)

Written before the training run starts. **What changes:** GRPO on top of the 82-task SFT (`sft_v3b_Qwen3.5-9B_20261026T124124Z_lr0.00024`, the version 4 row), with the version-3 recipe except for its size. About $14.5 of Tinker credit remains, so the run is 40 steps × **8** tasks × 8 rollouts (2,560 rollouts, 3.9 epochs over the 82 train tasks) with `max_tokens` 1,536, instead of 40 × 16 × 8 (5,120 rollouts, 8.9 epochs) with 2,048 in version 3. Learning rate 4e-5, LoRA rank 32, leak penalty 0.5, seed 0, dev evaluation and checkpoint every 10 steps, spend cap $13 (worst case $12.70, typical $7.15). One seed only; a second does not fit.

| Row | Run | Checkpoint | Why |
|---|---|---|---|
| sft-82+rl | rl_v3b_Qwen3.5-9B_lr4e-5_s40_b8 | highest dev pass rate (filled in when the run finishes) | the only run |

**Measures:** pass and leak over the 120 test samples with Wilson intervals; paired sign tests by task against `sft-82` (version 4), `sft-v3+rl` seed 0 (version 3) and `sft+rl` seed 0 (version 2), reused from their result files.

**What would count as a result:** a higher pass rate than `sft-82` with no higher leak rate. A half-size run that still beats its SFT would say the GRPO gain of version 3 does not depend on the larger batch; one that does not would be read as either the batch or the seed, which this budget cannot separate.

**Disclosure:** the fifth evaluation of the test split (versions 1–4 at 1bc6904, 54bb76a, 34bab1f, f1ae829). No training decision used test results.
