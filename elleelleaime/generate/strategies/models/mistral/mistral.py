from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy

from typing import Any, List

import os
import mistralai
import backoff


class MistralModels(PatchGenerationStrategy):
    def __init__(self, model_name: str, **kwargs) -> None:
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.0)
        self.n_samples = kwargs.get("n_samples", 1)

        self.client = mistralai.Mistral(os.getenv("MISTRAL_API_KEY", None))

    @backoff.on_exception(
        backoff.expo,
        (
            mistralai.models.SDKError,
            mistralai.models.HTTPValidationError,
            AssertionError,
        ),
    )
    def _completions_with_backoff(self, **kwargs):
        response = self.client.chat.complete(**kwargs)
        assert response is not None
        return response

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []

        for prompt in chunk:
            completion = self._completions_with_backoff(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                n=self.n_samples,
            )
            result.append(completion.model_dump())

        return result
