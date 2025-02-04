import getpass
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from unidiff import PatchSet

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.caching.cache import Cache
from elleelleaime.core.utils.java.java import remove_empty_lines, remove_java_comments
from elleelleaime.evaluate.strategies.strategy import PatchEvaluationStrategy


class ReplaceEvaluationStrategy(PatchEvaluationStrategy):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_cache = kwargs.get("use_cache", True)
        self.cache_path = kwargs.get(
            "cache_path", Path(__file__).parent.parent.parent.parent.parent / "cache"
        )
        if self.use_cache:
            self.cache = Cache(self.cache_path)

    def evaluate_generation(
        self, bug: Bug, sample: dict, generation: Optional[str]
    ) -> Optional[dict]:
        # If the generation is None, we skip the evaluation
        result = {
            "generation": generation,
            "exact_match": False,
            "ast_match": False,
            "compile": False,
            "test": False,
        }
        if generation is None:
            return result

        # Check if the evaluation is cached
        if self.use_cache:
            evaluation = self.cache.load_from_cache_from_bug(bug, generation)
            if evaluation is not None:
                return evaluation
            else:
                logging.info(
                    f"Evaluation for {bug.get_identifier()} not found in cache."
                )

        # Otherwise, we evaluate the generation
        buggy_path = os.path.join(
            tempfile.gettempdir(),
            f"elleelleaime-{getpass.getuser()}",
            bug.get_identifier(),
            str(uuid4()),
        )

        # Remove comments and empty lines from the generated code and the fixed code
        generation_no_comments = remove_java_comments(generation)
        if generation_no_comments is None:
            # Save the evaluation to the cache
            if self.use_cache:
                self.cache.save_to_cache_from_bug(bug, generation, result)
            return result
        generation_no_comments = remove_empty_lines(generation_no_comments)
        generation_no_comments = generation_no_comments.splitlines()
        fixed_code_no_comments = remove_empty_lines(
            remove_java_comments(sample["fixed_code"])
        )
        fixed_code_no_comments = fixed_code_no_comments.splitlines()

        result["exact_match"] = len(generation_no_comments) == len(
            fixed_code_no_comments
        ) and all(
            [
                x.strip() == y.strip()
                for x, y in zip(
                    generation_no_comments, fixed_code_no_comments, strict=True
                )
            ]
        )

        # If the generation is an exact match, there is no need to evaluate the AST, compile or test
        if result["exact_match"]:
            result["ast_match"] = True
            result["compile"] = True
            result["test"] = True

            # Save the evaluation to the cache
            if self.use_cache:
                self.cache.save_to_cache_from_bug(bug, generation, result)
            return result

        try:
            # Note: this diff is inverted, i.e. the target file is the buggy file
            diff = PatchSet(bug.get_ground_truth())

            # Checkout the buggy code
            bug.checkout(buggy_path, fixed=False)

            # Locate and load the buggy file
            if bug.is_ground_truth_inverted():
                buggy_file_path = os.path.join(
                    buggy_path,
                    (
                        diff[0].target_file[2:]
                        if diff[0].target_file.startswith("b/")
                        else diff[0].target_file
                    ),
                )
            else:
                buggy_file_path = os.path.join(
                    buggy_path,
                    (
                        diff[0].source_file[2:]
                        if diff[0].source_file.startswith("a/")
                        else diff[0].source_file
                    ),
                )

            with open(buggy_file_path, "r", encoding="ISO-8859-1") as f:
                buggy_code = f.read()

            # Check that buggy code exists
            if sample["buggy_code"] not in buggy_code:
                logging.error(
                    f"Could not find buggy code in {buggy_file_path} for {sample['identifier']}"
                )
                return None

            # Get the fixed and candidate code
            fixed_code = buggy_code.replace(sample["buggy_code"], sample["fixed_code"])
            candidate_code = buggy_code.replace(sample["buggy_code"], generation)

            # Compute plausible match
            # Write the generated code to the file
            with open(
                buggy_file_path,
                "w",
                encoding="ISO-8859-1",
                errors="replace",
            ) as f:
                f.write(candidate_code)

            # Evaluate the buggy code
            compilation_result = bug.compile(buggy_path)
            result["compile"] = compilation_result.is_passing()
            # If it compiles, test the code
            if result["compile"] or result["compile"] is None:
                test_result = bug.test(buggy_path)
                result["test"] = test_result.is_passing()
                # If the tests pass, check if the ASTs match
                # Note: we do not for AST matching before because the ast matcher returns false positives in some cases
                if result["test"]:
                    result["ast_match"] = self.ast_match(fixed_code, candidate_code)

            # Save the evaluation to the cache
            if self.use_cache:
                self.cache.save_to_cache_from_bug(bug, generation, result)
            return result
        finally:
            shutil.rmtree(buggy_path)

    def _evaluate_impl(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Returns the evaluation for the given bug and sample.

        :param bug: The bug to generate the prompt for.
        :param sample: The sample to evaluate.
        """
        evaluation = []

        for generation in sample["generation"]:
            evaluation.append(self.evaluate_generation(bug, sample, generation))

        return evaluation
