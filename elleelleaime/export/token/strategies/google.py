from typing import Optional
from .cost_strategy import TokenStrategy

import tqdm


class GoogleTokenStrategy(TokenStrategy):

    __COST_PER_MILLION_TOKENS = {
        "gemini-1.5-pro-001": {
            "prompt": 3.50,
            "completion": 10.50,
        },
        "gemini-1.5-pro-002": {
            "prompt": 1.25,
            "completion": 5.00,
        },
        "gemini-2.0-flash-001": {
            "prompt": 0.1,
            "completion": 0.4,
        },
    }

    __COST_PER_MILLION_TOKENS_OVER_128K = {
        "gemini-1.5-pro-001": {
            "prompt": 7.00,
            "completion": 21.00,
        },
        "gemini-1.5-pro-002": {
            "prompt": 2.50,
            "completion": 10.00,
        },
    }

    @staticmethod
    def compute_usage(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in GoogleTokenStrategy.__COST_PER_MILLION_TOKENS:
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
                for generation in sample["generation"]:
                    if "usage_metadata" not in generation:
                        continue

                    prompt_token_count = generation["usage_metadata"][
                        "prompt_token_count"
                    ]
                    completion_token_count = generation["usage_metadata"][
                        "candidates_token_count"
                    ]

                    # Update token counts
                    usage["prompt_tokens"] += prompt_token_count
                    usage["completion_tokens"] += completion_token_count

                    # Determine cost rates based on token count
                    if (
                        prompt_token_count > 128000
                        and model_name
                        in GoogleTokenStrategy.__COST_PER_MILLION_TOKENS_OVER_128K
                    ):
                        prompt_cost = (
                            GoogleTokenStrategy.__COST_PER_MILLION_TOKENS_OVER_128K[
                                model_name
                            ]["prompt"]
                        )
                        completion_cost = (
                            GoogleTokenStrategy.__COST_PER_MILLION_TOKENS_OVER_128K[
                                model_name
                            ]["completion"]
                        )
                    else:
                        prompt_cost = GoogleTokenStrategy.__COST_PER_MILLION_TOKENS[
                            model_name
                        ]["prompt"]
                        completion_cost = GoogleTokenStrategy.__COST_PER_MILLION_TOKENS[
                            model_name
                        ]["completion"]

                    # Calculate costs
                    usage["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    usage["completion_cost"] += (
                        completion_cost * completion_token_count / 1000000
                    )

        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        usage["total_cost"] = usage["prompt_cost"] + usage["completion_cost"]
        return usage
