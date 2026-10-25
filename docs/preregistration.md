# Pre-registration: version 2 test evaluation

Written before the version 2 test evaluation runs. Filled in with the chosen checkpoints at that point and
not edited after the evaluation starts; the test eval script records the git commit it ran at.

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
| sft+rl, seed 2 | _pending_ | | |
| repair | 20261025T194632Z (repair_Qwen3.5-9B_from40_s25) | step 5 | highest dev pass after 3 tries of the five evals (67%) |
| base (Nemotron) | nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16 | — | — |
| sft (Nemotron) | 20261025T190749Z (sft lr 3e-4) | final | lowest final dev loss of the three sweep runs (0.153) |
| sft+rl (Nemotron) | 20261025T193419Z (rl_Nemotron_lr6e-5_s50) | step 50 (final) | highest dev pass rate of the five evals (38%) |
| distil | _pending_ | | |

## Primary measures

1. Pass rate over all 120 test samples, with a 95% Wilson interval, per row.
2. Leak rate over all 120 test samples, per row.
3. Paired comparison by task (pass count out of 6, leak count out of 6) between consecutive rows, two-sided
   sign test.

## Secondary measures

Greedy pass@1 (n = 20), apply-error rate, format-error rate, mean answer length, pass and leak by tier, pass by
trap. For the repair row: pass rate after 1, 2 and 3 tries.

## What would count as a result

- A real improvement from RL: higher pass rate than the SFT row and no higher leak rate, with the paired
  comparison favouring RL on more tasks than it disfavours.
- Reward hacking signals, reported whichever way they come out: answers getting much shorter, tier 1
  improving while tiers 2–3 do not, greedy and sampled leak rates moving in opposite directions.

## Disclosure

The test split was evaluated once before, for version 1 (commit 1bc6904, 2026-10-25). No training decision
in version 2 used test results; checkpoints are chosen on dev only.
