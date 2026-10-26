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
| sft v3 + GRPO, seed 0 | _pending_ | | highest dev pass rate of the five evals |
| sft v3 + GRPO, seed 1 | _pending_ | | highest dev pass rate of the five evals |

**Measures:** as in version 2 (pass and leak over 120 test samples with Wilson intervals; paired sign tests by task against the version 2 rows `sft`, `sft+rl`, `sft+rl-seed1`, which are reused from `results/test_eval_v2/`, not re-run).

**What would count as a result:** version 3 SFT above version 2 SFT on test pass with no higher leak rate; and the GRPO-over-SFT comparison repeated with the new data, again reported whichever way it goes.

**Disclosure:** this is the third evaluation of the test split (version 1 at 1bc6904, version 2 at 54bb76a). No training decision used test results.
