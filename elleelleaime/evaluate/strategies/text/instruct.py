from .replace import ReplaceEvaluationStrategy
from elleelleaime.core.benchmarks.bug import Bug

from typing import Optional, List
import re


class InstructEvaluationStrategy(ReplaceEvaluationStrategy):

    def __init__(self, reverse: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.reverse = reverse

    def extract_patch_from_message(self, message: str) -> Optional[str]:
        """
        Extracts the generated code from the message.
        The generated code must be surrounded by backticks in Markdown style.
        The backticks could be ``` or ```java|python|etc.

        :param message: The message to extract the generated code from.
        """
        if message is None:
            return None

        # Pattern to match code blocks with or without language specifier
        pattern = re.compile(r"```(\w*)\n([\s\S]*?)\n```")

        code_blocks = []
        for match in pattern.finditer(message):
            language = match.group(1)  # Capture the language specifier
            code = match.group(2)  # Capture the code block content
            code_blocks.append((language, code))

        # Return the first or last code block depending on the reverse flag
        if self.reverse:
            return code_blocks[-1][1] if code_blocks else None
        else:
            return code_blocks[0][1] if code_blocks else None

    def _evaluate_impl(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Returns the evaluation for the given bug and sample.

        :param bug: The bug to generate the prompt for.
        :param sample: The sample to evaluate.
        """
        evaluation = []

        if sample["generation"] is None:
            return evaluation

        for generation in sample["generation"]:
            candidate_patch = self.extract_patch_from_message(generation)
            evaluation.append(self.evaluate_generation(bug, sample, candidate_patch))

        return evaluation
