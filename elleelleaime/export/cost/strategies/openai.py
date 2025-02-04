from typing import Optional

import tqdm

from .cost_strategy import CostStrategy


class OpenAICostStrategy(CostStrategy):

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
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in OpenAICostStrategy.__COST_PER_MILLION_TOKENS:
            return None

        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0,
        }

        for sample in tqdm.tqdm(samples, f"Computing costs for {model_name}..."):
            if sample["generation"]:
                if not isinstance(sample["generation"], list):
                    generation = [sample["generation"]]
                else:
                    generation = sample["generation"]
                for g in generation:
                    prompt_token_count = g["usage"]["prompt_tokens"]
                    candidates_token_count = g["usage"]["completion_tokens"]

                    prompt_cost = OpenAICostStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["prompt"]
                    completion_cost = OpenAICostStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["completion"]

                    costs["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    costs["completion_cost"] += (
                        completion_cost * candidates_token_count / 1000000
                    )

        costs["total_cost"] = costs["prompt_cost"] + costs["completion_cost"]
        return costs
