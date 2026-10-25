"""Tinker list prices, USD per 1M tokens, from thinkingmachines.ai/tinker/pricing as of 2026-10-19.

Shortest context tier for each model (the one the benchmark needs); rows the page showed at 50% off
are already discounted. Recheck before large runs. Every estimate in the training scripts uses this
table; the stored `est_spend_usd` figures are estimates from token counts, not invoices.
"""

PRICES: dict[str, dict[str, float]] = {
    "Qwen/Qwen3.5-9B": {"prefill": 0.30, "sample": 0.807, "train": 1.463},
    "Qwen/Qwen3.5-4B": {"prefill": 0.33, "sample": 1.005, "train": 0.737},
    "Qwen/Qwen3-8B": {"prefill": 0.195, "sample": 0.60, "train": 0.44},
    "Qwen/Qwen3.8-27B": {"prefill": 0.6975, "sample": 5.595, "train": 4.103},
    "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16": {"prefill": 0.184, "sample": 0.495, "train": 0.44},
    "deepseek-ai/DeepSeek-V4.1-Flash-1017": {"prefill": 0.60, "sample": 3.60, "train": 4.98},
    "moonshotai/Kimi-K2.6": {"prefill": 2.205, "sample": 5.49, "train": 4.84},
    "openai/gpt-oss-120b": {"prefill": 0.33, "sample": 0.84, "train": 0.737},
    "openai/gpt-oss-20b": {"prefill": 0.18, "sample": 0.45, "train": 0.396},
    "zai-org/GLM-5.3-Flash": {"prefill": 0.84, "sample": 2.11, "train": 5.58},
}

# Anthropic API, USD per 1M tokens (input, output), as of 2026-10-06; thinking tokens bill as output.
ANTHROPIC_PRICES: dict[str, dict[str, float]] = {
    "claude-opus-5-5": {"input": 4.0, "output": 20.0},
    "claude-sonnet-5-5": {"input": 2.0, "output": 10.0},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50},
}


def price(model: str) -> dict[str, float]:
    if model not in PRICES:
        raise KeyError(f"no Tinker price on file for {model}; add it to train/prices.py from the pricing page")
    return PRICES[model]


def rollout_usd(prompt_tokens: int, completion_tokens: int, model: str, *, train: bool) -> float:
    """Cost of sampling one completion, plus training on it when `train`."""
    p = price(model)
    usd = prompt_tokens * p["prefill"] + completion_tokens * p["sample"]
    if train:
        usd += (prompt_tokens + completion_tokens) * p["train"]
    return usd / 1e6
