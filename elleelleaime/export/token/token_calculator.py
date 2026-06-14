from .strategies.openai import OpenAITokenStrategy
from .strategies.google import GoogleTokenStrategy
from .strategies.openrouter import OpenRouterTokenStrategy
from .strategies.anthropic import AnthropicTokenStrategy
from .strategies.mistral import MistralTokenStrategy
from typing import Optional


class TokenCalculator:

    __TOKEN_STRATEGIES = {
        "openai-chatcompletion": OpenAITokenStrategy,
        "google": GoogleTokenStrategy,
        "openrouter": OpenRouterTokenStrategy,
        "anthropic": AnthropicTokenStrategy,
        "mistral": MistralTokenStrategy,
    }

    @staticmethod
    def compute_usage(samples: list, provider: str, model_name: str) -> Optional[dict]:
        strategy = TokenCalculator.__TOKEN_STRATEGIES.get(provider)
        if strategy is None:
            return None
        return strategy.compute_usage(samples, model_name)
