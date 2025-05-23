from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy

from typing import Any, List

import os
import anthropic
import backoff


class AnthropicModels(PatchGenerationStrategy):
    def __init__(self, model_name: str, max_tokens: int, **kwargs) -> None:
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = kwargs.get("temperature", 0.0)
        self.n_samples = kwargs.get("n_samples", 1)

        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
        raise_on_giveup=False,
    )
    def _completions_with_backoff(self, **kwargs):
        return self.client.messages.create(**kwargs)

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []

        for prompt in chunk:
            result_sample = []
            for _ in range(self.n_samples):
                completion = self._completions_with_backoff(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                )
                if completion:
                    result_sample.append(completion.to_dict())
                else:
                    result_sample.append(completion)
            result.append(result_sample)

        return result
