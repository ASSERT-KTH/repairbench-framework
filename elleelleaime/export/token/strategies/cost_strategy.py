from typing import Optional
from abc import ABC, abstractmethod


class TokenStrategy(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @staticmethod
    @abstractmethod
    def compute_usage(samples: list, model_name: str) -> Optional[dict]:
        """
        Computes token usage and cost information for the given samples
        Returns a dictionary containing:
        - prompt_tokens: number of tokens in prompts
        - completion_tokens: number of tokens in completions
        - total_tokens: total number of tokens
        - cost: total cost in USD
        """
        pass


class CostStrategy(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @staticmethod
    @abstractmethod
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        pass
