import google.api_core
import google.api_core.exceptions
from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy

from typing import Any, List

import os
import tqdm
import google.generativeai as genai
import google
import backoff

import google.api


class GoogleModels(PatchGenerationStrategy):
    def __init__(self, model_name: str, **kwargs) -> None:
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)
        self.temperature = kwargs.get("temperature", 0.0)
        self.n_samples = kwargs.get("n_samples", 1)

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def __get_config(self):
        return genai.types.GenerationConfig(
            temperature=self.temperature,
        )

    @backoff.on_exception(backoff.expo, google.api_core.exceptions.ResourceExhausted)
    def __generate_with_backoff(self, prompt: str) -> dict:
        completion = self.model.generate_content(
            prompt, generation_config=self.__get_config()
        )
        return completion.to_dict()

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []

        for prompt in tqdm.tqdm(chunk, "Generating patches for prompt..."):
            p_results = []
            for _ in range(self.n_samples):
                p_results.append(self.__generate_with_backoff(prompt))
            result.append(p_results)

        return result
