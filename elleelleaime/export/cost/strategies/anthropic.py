import logging
from typing import Optional

import tqdm

from .cost_strategy import CostStrategy


class AnthropicCostStrategy(CostStrategy):

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
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in AnthropicCostStrategy.__COST_PER_MILLION_TOKENS:
            return None

        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0,
        }

        for sample in tqdm.tqdm(samples, f"Computing costs for {model_name}..."):
            if sample["generation"]:
                for g in sample["generation"]:
                    if "usage" not in g:
                        logging.warning(
                            f"No usage found for sample: {sample['identifier']}"
                        )
                        continue
                    prompt_token_count = g["usage"]["input_tokens"]
                    candidates_token_count = g["usage"]["output_tokens"]

                    prompt_cost = AnthropicCostStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["prompt"]
                    completion_cost = AnthropicCostStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["completion"]

                    costs["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    costs["completion_cost"] += (
                        completion_cost * candidates_token_count / 1000000
                    )

        costs["total_cost"] = costs["prompt_cost"] + costs["completion_cost"]
        return costs
