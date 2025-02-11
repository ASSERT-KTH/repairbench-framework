from typing import Optional
from .cost_strategy import TokenStrategy

import tqdm
import logging


class OpenRouterTokenStrategy(TokenStrategy):

    __COST_PER_MILLION_TOKENS = {
        "meta-llama:llama-3.1-405b-instruct": {
            "prompt": 2.8,
            "completion": 2.8,
        },
        "deepseek-v2.5": {
            "prompt": 2,
            "completion": 2,
        },
        "mistral-large-2407": {
            "prompt": 2,
            "completion": 6,
        },
        "qwen-2.5-72b-instruct": {
            "prompt": 0.35,
            "completion": 0.4,
        },
        "llama-3.1-nemotron-70b-instruct": {
            "prompt": 0.35,
            "completion": 0.4,
        },
        "qwen-2.5-coder-32b-instruct": {
            "prompt": 0.2,
            "completion": 0.2,
        },
        "qwq-32b-preview": {
            "prompt": 0.15,
            "completion": 0.6,
        },
        "llama-3.3-70b-instruct": {
            "prompt": 0.13,
            "completion": 0.4,
        },
        "grok-2-1212": {
            "prompt": 2.0,
            "completion": 10.0,
        },
        "deepseek-v3": {
            "prompt": 0.14,
            "completion": 0.28,
        },
        "deepseek-r1": {
            "prompt": 0.55,
            "completion": 2.19,
        },
        "deepseek-r1-distill-llama-70b": {
            "prompt": 0.23,
            "completion": 0.69,
        },
        "deepseek-r1-distill-qwen-32b": {
            "prompt": 0.12,
            "completion": 0.18,
        },
    }

    @staticmethod
    def compute_usage(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in OpenRouterTokenStrategy.__COST_PER_MILLION_TOKENS:
            return None

        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0,
        }

        for sample in tqdm.tqdm(samples, f"Computing token usage for {model_name}..."):
            if sample["generation"]:
                if not isinstance(sample["generation"], list):
                    generation = [sample["generation"]]
                else:
                    generation = sample["generation"]

                for g in generation:
                    if not g:
                        logging.warning(f"generation is empty")
                        continue
                    elif "usage" not in g:
                        logging.warning(f"'usage' key not found in {g}")
                        continue

                    prompt_token_count = g["usage"]["prompt_tokens"]
                    completion_token_count = g["usage"]["completion_tokens"]

                    # Update token counts
                    usage["prompt_tokens"] += prompt_token_count
                    usage["completion_tokens"] += completion_token_count

                    # Calculate costs
                    prompt_cost = OpenRouterTokenStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["prompt"]
                    completion_cost = OpenRouterTokenStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["completion"]

                    usage["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    usage["completion_cost"] += (
                        completion_cost * completion_token_count / 1000000
                    )

        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        usage["total_cost"] = usage["prompt_cost"] + usage["completion_cost"]
        return usage
