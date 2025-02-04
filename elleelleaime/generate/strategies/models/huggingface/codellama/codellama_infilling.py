import logging
import threading
from dataclasses import dataclass
from typing import Any, List, Optional

import torch
import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.tokenization_utils_base import PreTrainedTokenizerBase

from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy


@dataclass
class GenerateSettings:
    name: str
    do_sample: bool = False
    temperature: float = 1.0
    num_beams: int = 1
    num_return_sequences: int = 10
    max_length: int = 4096
    early_stopping: bool = True


class CodeLLaMAInfilling(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        "codellama/CodeLlama-7b-hf",
        "codellama/CodeLlama-13b-hf",
        "codellama/CodeLlama-34b-hf",
        "codellama/CodeLlama-70b-hf",
        "meta-llama/CodeLlama-7b-hf",
        "meta-llama/CodeLlama-13b-hf",
        "meta-llama/CodeLlama-34b-hf",
        "meta-llama/CodeLlama-70b-hf",
    }

    __GENERATION_STRATEGIES = {
        "beam_search": GenerateSettings(
            name="beam_search",
            early_stopping=True,
        ),
        "sampling": GenerateSettings(
            name="sampling",
            do_sample=True,
        ),
    }

    __MODEL = None
    __TOKENIZER = None
    __MODELS_LOADED: bool = False
    __MODELS_LOCK: threading.Lock = threading.Lock()

    def __init__(self, model_name: str, **kwargs) -> None:
        assert (
            model_name in self.__SUPPORTED_MODELS
        ), f"Model {model_name} not supported by {self.__class__.__name__}"
        self.model_name = model_name
        # Generation settings
        assert (
            kwargs.get("generation_strategy", "beam_search")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'beam_search')} not supported by {self.__class__.__name__}"
        self.generate_settings = self.__GENERATION_STRATEGIES[
            kwargs.get("generation_strategy", "beam_search")
        ]
        self.generate_settings.num_return_sequences = kwargs.get(
            "num_return_sequences", GenerateSettings.num_return_sequences
        )
        self.generate_settings.num_beams = kwargs.get(
            "num_beams", GenerateSettings.num_beams
        )
        self.generate_settings.temperature = kwargs.get(
            "temperature", GenerateSettings.temperature
        )
        self.__load_model()

    def __load_model(self):
        # Setup environment
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.context_size = self.generate_settings.max_length

        # Setup kwargs
        kwargs = dict(
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )

        # Load the model and tokenizer
        with self.__MODELS_LOCK:
            if self.__MODELS_LOADED:
                return
            self.__TOKENIZER: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
                self.model_name
            )
            self.__MODEL = AutoModelForCausalLM.from_pretrained(
                self.model_name, **kwargs
            )
            self.__MODEL.eval()
            self.__MODELS_LOADED = True

    def __generate_patch(self, prompt: str) -> Optional[List[str]]:
        if prompt.count("<FILL_ME>") > 1:
            logging.warning(
                "Prompt should contain exactly at most one <FILL_ME> tag, but it contains %d. Skipping bug.",
                prompt.count("<FILL_ME>"),
            )
            return None

        inputs = self.__TOKENIZER(prompt, return_tensors="pt").to(self.device)

        input_len = inputs["input_ids"].shape[1]
        if input_len >= self.context_size:
            logging.warning(
                f"warning: input_len ({input_len}) is greater than the context window {self.context_size}"
            )
            return None

        with torch.no_grad():
            generated_ids = self.__MODEL.generate(
                **inputs,
                max_length=self.generate_settings.max_length,
                num_beams=self.generate_settings.num_beams,
                num_return_sequences=self.generate_settings.num_return_sequences,
                early_stopping=self.generate_settings.early_stopping,
                do_sample=self.generate_settings.do_sample,
                temperature=self.generate_settings.temperature,
                use_cache=True,
            )

        fillings_ids = generated_ids[:, input_len:]
        fillings = self.__TOKENIZER.batch_decode(fillings_ids, skip_special_tokens=True)

        if "<FILL_ME>" in prompt:
            return [prompt.replace("<FILL_ME>", filling) for filling in fillings]
        else:
            return list(fillings)

    def _generate_impl(self, prompts: List[str]) -> Any:
        return [
            self.__generate_patch(p)
            for p in tqdm.tqdm(prompts, "Generating patches...", total=len(prompts))
        ]
