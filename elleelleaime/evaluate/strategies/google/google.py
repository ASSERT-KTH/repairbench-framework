from elleelleaime.evaluate.strategies.text.instruct import InstructEvaluationStrategy
from elleelleaime.core.benchmarks.bug import Bug

from typing import Optional, List


class GoogleEvaluationStrategy(InstructEvaluationStrategy):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
            for candidate in generation["candidates"]:
                if (
                    "content" not in candidate
                    or "parts" not in candidate["content"]
                    or not candidate["content"]["parts"]
                    or "text" not in candidate["content"]["parts"][0]
                ):
                    evaluation.append(None)
                    continue
                candidate_patch = candidate["content"]["parts"][0]["text"]
                candidate_patch = self.extract_patch_from_message(candidate_patch)
                evaluation.append(
                    self.evaluate_generation(bug, sample, candidate_patch)
                )

        return evaluation
