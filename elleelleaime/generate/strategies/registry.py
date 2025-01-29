from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from elleelleaime.generate.strategies.models.openai.openai import (
    OpenAIChatCompletionModels,
)
from elleelleaime.generate.strategies.models.google.google import (
    GoogleModels,
)
from elleelleaime.generate.strategies.models.huggingface.codellama.codellama_infilling import (
    CodeLLaMAInfilling,
)
from elleelleaime.generate.strategies.models.huggingface.codellama.codellama_instruct import (
    CodeLLaMAIntruct,
)
from elleelleaime.generate.strategies.models.openrouter.openrouter import (
    OpenRouterModels,
)
from elleelleaime.generate.strategies.models.anthropic.anthropic import (
    AnthropicModels,
)
from elleelleaime.generate.strategies.models.mistral.mistral import (
    MistralModels,
)
from elleelleaime.generate.strategies.models.huggingface.deepseek.deepseek_fim import (
    DeepSeekFIM,
)

from typing import Tuple


class PatchGenerationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    # The registry is a dict of strategy names to a tuple of class and mandatory arguments to init the class
    # NOTE: Do not instantiate the model here, as we should only instanciate the class to be used
    __MODELS: dict[str, Tuple[type, Tuple]] = {
        "openai-chatcompletion": (OpenAIChatCompletionModels, ("model_name",)),
        "google": (GoogleModels, ("model_name",)),
        "openrouter": (OpenRouterModels, ("model_name",)),
        "codellama-infilling": (CodeLLaMAInfilling, ("model_name",)),
        "codellama-instruct": (CodeLLaMAIntruct, ("model_name",)),
        "anthropic": (AnthropicModels, ("model_name", "max_tokens")),
        "mistral": (MistralModels, ("model_name",)),
        "deepseek-fim": (DeepSeekFIM, ("model_name",)),
    }

    @classmethod
    def get_generation(cls, name: str, **kwargs) -> PatchGenerationStrategy:
        if name.lower().strip() not in cls.__MODELS:
            raise ValueError(f"Unknown strategy {name}")

        strategy_class, strategy_args = cls.__MODELS[name.lower().strip()]
        for strategy_arg in strategy_args:
            if strategy_arg not in kwargs:
                raise ValueError(f"Missing argument {strategy_arg} for strategy {name}")
        return strategy_class(**kwargs)
