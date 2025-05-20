from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from typing import Any, List

import backoff, litellm, logging

logging.getLogger("LiteLLM").setLevel(logging.WARNING)


class LiteLLMChatCompletionModels(PatchGenerationStrategy):
    def __init__(self, **kwargs) -> None:
        self.n_samples = kwargs.pop("n_samples", 1)
        self.kwargs = kwargs

    @backoff.on_exception(backoff.expo, Exception)
    def _completions_with_backoff(self, **kwargs):
        response = litellm.completion(
            **kwargs, seed=42, caching=False, cache={"no-cache": True, "no-store": True}
        )
        return response.choices[0].message.content

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []
        for prompt in chunk:
            result_sample = []
            for _ in range(self.n_samples):
                completion = self._completions_with_backoff(
                    messages=[{"role": "user", "content": prompt}], **self.kwargs
                )
                result_sample.append(completion)
            result.append(result_sample)

        return result
