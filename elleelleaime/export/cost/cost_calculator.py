from typing import Optional

from .strategies.anthropic import AnthropicCostStrategy
from .strategies.google import GoogleCostStrategy
from .strategies.mistral import MistralCostStrategy
from .strategies.openai import OpenAICostStrategy
from .strategies.openrouter import OpenRouterCostStrategy


class CostCalculator:

    __COST_STRATEGIES = {
        "openai-chatcompletion": OpenAICostStrategy,
        "google": GoogleCostStrategy,
        "openrouter": OpenRouterCostStrategy,
        "anthropic": AnthropicCostStrategy,
        "mistral": MistralCostStrategy,
    }

    @staticmethod
    def compute_costs(samples: list, provider: str, model_name: str) -> Optional[dict]:
        strategy = CostCalculator.__COST_STRATEGIES.get(provider)
        if strategy is None:
            return None
        return strategy.compute_costs(samples, model_name)
