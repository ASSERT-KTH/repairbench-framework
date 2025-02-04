import logging
from dataclasses import dataclass
from typing import Any, List

import torch
import tqdm
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy


@dataclass
class GenerateSettings:
    name: str
    do_sample: bool = False
    temperature: float = 1.0
    num_beams: int = 1
    num_return_sequences: int = 10
    max_length: int = 16384
    early_stopping: bool = True


class CodeLLaMAIntruct(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        "meta-llama/CodeLlama-7b-Instruct-hf",
        "meta-llama/CodeLlama-13b-Instruct-hf",
        "meta-llama/CodeLlama-34b-Instruct-hf",
        "meta-llama/CodeLlama-70b-Instruct-hf",
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

    def __init__(self, model_name: str, **kwargs) -> None:
        assert (
            model_name in self.__SUPPORTED_MODELS
        ), f"Model {model_name} not supported by {self.__class__.__name__}"
        self.model_name = model_name
        self.adapter_name = kwargs.get("adapter_name", None)

        # Setup generation settings
        assert (
            kwargs.get("generation_strategy", "sampling")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'sampling')} not supported by {self.__class__.__name__}"

        self.generate_settings = self.__GENERATION_STRATEGIES[
            kwargs.get("generation_strategy", "sampling")
        ]
        self.batch_size = kwargs.get("batch_size", 1)
        self.generate_settings.num_return_sequences = kwargs.get(
            "num_return_sequences", GenerateSettings.num_return_sequences
        )
        self.generate_settings.num_beams = kwargs.get(
            "num_beams", GenerateSettings.num_beams
        )
        self.generate_settings.temperature = kwargs.get(
            "temperature", GenerateSettings.temperature
        )
        self.generate_settings.max_length = kwargs.get(
            "max_length", GenerateSettings.max_length
        )

    def __format_prompt(self, prompt: str) -> str:
        return f"<s>[INST] {prompt} [\\INST]"

    def _generate_impl(self, chunk: List[str]) -> Any:
        # Load model and tokenizer
        m = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        # Load LoRA adapter if specified
        if self.adapter_name:
            m = PeftModel.from_pretrained(m, self.adapter_name)
            m = m.merge_and_unload()
        m.eval()

        tok = AutoTokenizer.from_pretrained(self.model_name)
        tok.pad_token = tok.eos_token

        logging.info(f"Model successfully loaded: {m}")

        # Generate patches
        logging.info(f"Starting generation: {self.generate_settings}")
        result = []
        for prompt in tqdm.tqdm(chunk, "Generating patches...", total=len(chunk)):
            with torch.no_grad():
                # Tokenize prompt
                inputs = tok(self.__format_prompt(prompt), return_tensors="pt")

                # Skip prompt if it is too long
                input_length = inputs["input_ids"].shape[1]
                if input_length > self.generate_settings.max_length:
                    result.append(None)
                    logging.warning(
                        f"Skipping prompt due to length: {input_length} is larger than {self.generate_settings.max_length}"
                    )
                    continue

                # Generate patch
                inputs = inputs.to("cuda")
                outputs = m.generate(
                    **inputs,
                    max_length=self.generate_settings.max_length,
                    num_beams=self.generate_settings.num_beams,
                    num_return_sequences=self.generate_settings.num_return_sequences,
                    early_stopping=self.generate_settings.early_stopping,
                    do_sample=self.generate_settings.do_sample,
                    temperature=self.generate_settings.temperature,
                    use_cache=True,
                )

                # Decode outputs and save
                responses = tok.batch_decode(outputs, skip_special_tokens=True)
                responses = [r.split("[\\INST]")[1] for r in responses]
                result.append(responses)

        # Return results
        return result
