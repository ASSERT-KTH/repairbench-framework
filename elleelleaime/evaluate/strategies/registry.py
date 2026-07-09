from elleelleaime.evaluate.strategies.strategy import PatchEvaluationStrategy
from elleelleaime.evaluate.strategies.text.replace import ReplaceEvaluationStrategy
from elleelleaime.evaluate.strategies.text.instruct import InstructEvaluationStrategy
from elleelleaime.evaluate.strategies.text.replace_python import (
    ReplaceEvaluationStrategyPython,
)
from elleelleaime.evaluate.strategies.text.instruct_python import (
    InstructEvaluationStrategyPython,
)
from elleelleaime.evaluate.strategies.openai.openai import OpenAIEvaluationStrategy
from elleelleaime.evaluate.strategies.openai.openai_python import (
    OpenAIEvaluationStrategyPython,
)
from elleelleaime.evaluate.strategies.google.google import GoogleEvaluationStrategy
from elleelleaime.evaluate.strategies.google.google_python import (
    GoogleEvaluationStrategyPython,
)
from elleelleaime.evaluate.strategies.openrouter.openrouter import (
    OpenRouterEvaluationStrategy,
)
from elleelleaime.evaluate.strategies.openrouter.openrouter_python import (
    OpenRouterEvaluationStrategyPython,
)
from elleelleaime.evaluate.strategies.anthropic.anthropic import (
    AnthropicEvaluationStrategy,
)
from elleelleaime.evaluate.strategies.anthropic.anthropic_python import (
    AnthropicEvaluationStrategyPython,
)
from elleelleaime.evaluate.strategies.mistral.mistral import MistralEvaluationStrategy
from elleelleaime.evaluate.strategies.mistral.mistral_python import (
    MistralEvaluationStrategyPython,
)


class PatchEvaluationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    def __init__(self, **kwargs):
        self._strategies: dict[str, PatchEvaluationStrategy] = {
            "replace": ReplaceEvaluationStrategy(**kwargs),
            "instruct": InstructEvaluationStrategy(**kwargs),
            "replace_python": ReplaceEvaluationStrategyPython(**kwargs),
            "instruct_python": InstructEvaluationStrategyPython(**kwargs),
            "openai": OpenAIEvaluationStrategy(**kwargs),
            "openai_python": OpenAIEvaluationStrategyPython(**kwargs),
            "google": GoogleEvaluationStrategy(**kwargs),
            "google_python": GoogleEvaluationStrategyPython(**kwargs),
            "openrouter": OpenRouterEvaluationStrategy(**kwargs),
            "openrouter_python": OpenRouterEvaluationStrategyPython(**kwargs),
            "anthropic": AnthropicEvaluationStrategy(**kwargs),
            "anthropic_python": AnthropicEvaluationStrategyPython(**kwargs),
            "mistral": MistralEvaluationStrategy(**kwargs),
            "mistral_python": MistralEvaluationStrategyPython(**kwargs),
        }

    def get_evaluation(self, name: str) -> PatchEvaluationStrategy:
        if name.lower().strip() not in self._strategies:
            raise ValueError(f"Unknown strategy {name}")
        return self._strategies[name.lower().strip()]
