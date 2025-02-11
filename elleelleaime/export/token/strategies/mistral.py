from typing import Optional
from .cost_strategy import TokenStrategy

import tqdm


class MistralTokenStrategy(TokenStrategy):

    __COST_PER_MILLION_TOKENS = {
        "mistral-large-2411": {
            "prompt": 2,
            "completion": 6,
        },
        "codestral-2405": {
            "prompt": 0.2,
            "completion": 0.6,
        },
        "codestral-2501": {
            "prompt": 0.3,
            "completion": 0.9,
        },
    }

    @staticmethod
    def compute_usage(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in MistralTokenStrategy.__COST_PER_MILLION_TOKENS:
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
                g = sample["generation"]
                prompt_token_count = g["usage"]["prompt_tokens"]
                completion_token_count = g["usage"]["completion_tokens"]

                # Update token counts
                usage["prompt_tokens"] += prompt_token_count
                usage["completion_tokens"] += completion_token_count

                # Calculate costs
                prompt_cost = MistralTokenStrategy.__COST_PER_MILLION_TOKENS[
                    model_name
                ]["prompt"]
                completion_cost = MistralTokenStrategy.__COST_PER_MILLION_TOKENS[
                    model_name
                ]["completion"]

                usage["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                usage["completion_cost"] += (
                    completion_cost * completion_token_count / 1000000
                )

        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        usage["total_cost"] = usage["prompt_cost"] + usage["completion_cost"]
        return usage
