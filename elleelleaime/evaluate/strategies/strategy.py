import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Any, List, Optional, final

from elleelleaime.core.benchmarks.bug import Bug


class PatchEvaluationStrategy(ABC):
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def _evaluate_impl(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Implemenation method for the evaluation strategy.
        """
        pass

    @final
    def __handle_none(self) -> Any:
        """
        Handles the case where the generation is None. For now, we simply return None.
        """
        return None

    def ast_match(self, fixed_code: str, candidate_code: str) -> bool:
        # Write the fixed code to a temporary file
        fixed_code_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".java", delete=True
        )
        fixed_code_file.write(fixed_code)
        fixed_code_file.flush()

        # Write the candidate code to a temporary file
        candidate_code_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".java", delete=True
        )
        candidate_code_file.write(candidate_code)
        candidate_code_file.flush()

        # Run the AST matcher on the two files
        run = subprocess.run(
            f'docker run --rm --volume ".:/elleelleaime" --volume "{tempfile.gettempdir()}:{tempfile.gettempdir()}" --workdir "/elleelleaime" openjdk:11 java -jar gumtree-spoon-ast-diff.jar {fixed_code_file.name} {candidate_code_file.name}',
            shell=True,
            capture_output=True,
        )

        # Return True if "no AST change" in the output
        return "no AST change" in run.stdout.decode("utf-8")

    @final
    def evaluate(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Returns the evaluation results for the given sample.

        :param sample: The sample to evaluate.
        :return: A dictionary containing the evaluation results.
        """
        # Implements the logic common to all generation strategies
        if "generation" not in sample or sample["generation"] is None:
            return self.__handle_none()

        return self._evaluate_impl(bug, sample)
