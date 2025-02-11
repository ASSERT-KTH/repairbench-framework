from typing import Optional
from .cost_strategy import TokenStrategy

import tqdm


class OpenAITokenStrategy(TokenStrategy):

    __COST_PER_MILLION_TOKENS = {
        "gpt-4o-2024-08-06": {
            "prompt": 2.5,
            "completion": 10,
        },
        "gpt-4o-2024-11-20": {
            "prompt": 2.5,
            "completion": 10,
        },
        "o1-preview-2024-09-12": {
            "prompt": 15,
            "completion": 60,
        },
        "o3-mini-2025-01-31": {
            "prompt": 1.1,
            "completion": 4.4,
        },
    }

    @staticmethod
    def compute_usage(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in OpenAITokenStrategy.__COST_PER_MILLION_TOKENS:
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
                    prompt_token_count = g["usage"]["prompt_tokens"]
                    completion_token_count = g["usage"]["completion_tokens"]

                    # Update token counts
                    usage["prompt_tokens"] += prompt_token_count
                    usage["completion_tokens"] += completion_token_count

                    # Calculate costs
                    prompt_cost = OpenAITokenStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["prompt"]
                    completion_cost = OpenAITokenStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["completion"]

                    usage["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    usage["completion_cost"] += (
                        completion_cost * completion_token_count / 1000000
                    )

        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        usage["total_cost"] = usage["prompt_cost"] + usage["completion_cost"]
        return usage
