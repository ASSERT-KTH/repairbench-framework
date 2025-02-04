from typing import Optional, Tuple

from unidiff import PatchSet

from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.utils.java.java import (
    extract_failing_test_cases,
    extract_single_function,
)
from elleelleaime.sample.strategy import PromptingStrategy


class InstructPrompting(PromptingStrategy):
    """
    Implements instruction prompting strategies.
    """

    def __init__(self, **kwargs):
        super().__init__("instruct")

    def instruct(
        self, bug: RichBug
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Builds an instruction prompt for the given bug.

        Args:
            bug: The bug to generate the prompt for.
        Returns:
            Tuple: A tuple of the form (buggy_code, fixed_code, prompt).
        """
        result = extract_single_function(bug)
        if result is None:
            return None, None, None

        buggy_code, fixed_code = result

        failing_test_cases = extract_failing_test_cases(bug)
        failing_test_causes = bug.get_failing_tests()
        if len(failing_test_causes) == 0 or len(failing_test_cases) == 0:
            return None, None, None

        failing_tests_string = ""
        for test_case in failing_test_cases.keys():
            failing_tests_string += f"""Test `{test_case}`:
```java
{failing_test_cases[test_case]}
```
Test `{test_case}` error:
```
{failing_test_causes[test_case]}
```

"""

        prompt = f"""You are an automatic program repair tool. Your task is to fix the provided buggy code.

The following code contains a buggy function:
```java
{buggy_code}
```

The code fails the following tests.

{failing_tests_string}
Please provide a fixed version of the buggy function, and only that function, inside a code block.
"""

        return buggy_code, fixed_code, prompt

    def prompt(self, bug: RichBug) -> dict[str, Optional[str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        """
        result = {
            "identifier": bug.get_identifier(),
            "buggy_code": None,
            "fixed_code": None,
            "prompt_strategy": self.strategy_name,
            "prompt": None,
            "ground_truth": bug.get_ground_truth(),
        }

        diff = PatchSet(bug.get_ground_truth())

        # This strategy only supports single-file prompts
        if len(diff) != 1:
            return result

        (
            result["buggy_code"],
            result["fixed_code"],
            result["prompt"],
        ) = self.instruct(bug)
        return result
