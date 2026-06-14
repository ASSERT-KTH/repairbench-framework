from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from typing import Any, List

import backoff, litellm, logging

logging.getLogger("LiteLLM").setLevel(logging.WARNING)


class LiteLLMChatCompletionModels(PatchGenerationStrategy):
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    @backoff.on_exception(backoff.expo, Exception)
    def _completions_with_backoff(self, **kwargs):
        return litellm.completion(
            **kwargs, caching=False, cache={"no-cache": True, "no-store": True}
        )

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []
        for prompt in chunk:
            completion = self._completions_with_backoff(
                messages=[{"role": "user", "content": prompt}], **self.kwargs
            )
            result.append(completion.to_dict())
        return result
