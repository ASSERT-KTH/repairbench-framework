from typing import Optional
from .cost_strategy import TokenStrategy

import tqdm
import logging


class AnthropicTokenStrategy(TokenStrategy):

    __COST_PER_MILLION_TOKENS = {
        "claude-3-5-sonnet-20240620": {
            "prompt": 3,
            "completion": 15,
        },
        "claude-3-5-sonnet-20241022": {
            "prompt": 3,
            "completion": 15,
        },
        "claude-3-haiku-20240307": {
            "prompt": 0.25,
            "completion": 1.25,
        },
    }

    @staticmethod
    def compute_usage(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in AnthropicTokenStrategy.__COST_PER_MILLION_TOKENS:
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
                for g in sample["generation"]:
                    if "usage" not in g:
                        logging.warning(
                            f"No usage found for sample: {sample['identifier']}"
                        )
                        continue
                    prompt_token_count = g["usage"]["input_tokens"]
                    completion_token_count = g["usage"]["output_tokens"]

                    # Update token counts
                    usage["prompt_tokens"] += prompt_token_count
                    usage["completion_tokens"] += completion_token_count

                    # Calculate costs
                    prompt_cost = AnthropicTokenStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["prompt"]
                    completion_cost = AnthropicTokenStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["completion"]

                    usage["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    usage["completion_cost"] += (
                        completion_cost * completion_token_count / 1000000
                    )

        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        usage["total_cost"] = usage["prompt_cost"] + usage["completion_cost"]
        return usage
