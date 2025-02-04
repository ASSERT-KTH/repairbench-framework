from elleelleaime.evaluate.strategies.anthropic.anthropic import (
    AnthropicEvaluationStrategy,
)
from elleelleaime.evaluate.strategies.google.google import GoogleEvaluationStrategy
from elleelleaime.evaluate.strategies.mistral.mistral import MistralEvaluationStrategy
from elleelleaime.evaluate.strategies.openai.openai import OpenAIEvaluationStrategy
from elleelleaime.evaluate.strategies.openrouter.openrouter import (
    OpenRouterEvaluationStrategy,
)
from elleelleaime.evaluate.strategies.strategy import PatchEvaluationStrategy
from elleelleaime.evaluate.strategies.text.instruct import InstructEvaluationStrategy
from elleelleaime.evaluate.strategies.text.replace import ReplaceEvaluationStrategy


class PatchEvaluationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    def __init__(self, **kwargs):
        self._strategies: dict[str, PatchEvaluationStrategy] = {
            "replace": ReplaceEvaluationStrategy(**kwargs),
            "instruct": InstructEvaluationStrategy(**kwargs),
            "openai": OpenAIEvaluationStrategy(**kwargs),
            "google": GoogleEvaluationStrategy(**kwargs),
            "openrouter": OpenRouterEvaluationStrategy(**kwargs),
            "anthropic": AnthropicEvaluationStrategy(**kwargs),
            "mistral": MistralEvaluationStrategy(**kwargs),
        }

    def get_evaluation(self, name: str) -> PatchEvaluationStrategy:
        if name.lower().strip() not in self._strategies:
            raise ValueError(f"Unknown strategy {name}")
        return self._strategies[name.lower().strip()]
