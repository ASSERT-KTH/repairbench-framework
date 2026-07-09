from typing import Optional, List
from unidiff import PatchSet
from pathlib import Path
from uuid import uuid4

import os, tempfile, shutil, logging, getpass, subprocess

from elleelleaime.evaluate.strategies.strategy import PatchEvaluationStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.python.python import (
    remove_python_comments,
    remove_empty_lines,
)
from elleelleaime.core.caching.cache import Cache


class ReplaceEvaluationStrategyPython(PatchEvaluationStrategy):

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

        # Remove comments and empty lines from the generated code and the fixed code
        generation_no_comments = remove_python_comments(generation)
        if generation_no_comments is None:
            # Save the evaluation to the cache
            if self.use_cache:
                self.cache.save_to_cache_from_bug(bug, generation, result)
            return result
        generation_no_comments = remove_empty_lines(generation_no_comments)
        generation_no_comments = generation_no_comments.splitlines()
        fixed_code_no_comments = remove_empty_lines(
            remove_python_comments(sample["fixed_code"])
        )
        if fixed_code_no_comments is None:
            # Save the evaluation to the cache
            if self.use_cache:
                self.cache.save_to_cache_from_bug(bug, generation, result)
            return result
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
            # For BugsInPy, we need to work with Docker
            project_name = bug.project_name
            bug_id = bug.bug_id

            # Checkout the buggy version inside the container
            if hasattr(bug, "checkout_fixed"):
                bug.checkout_fixed(bug.get_identifier(), fixed=False)
            else:
                bug.checkout(bug.get_identifier(), fixed=False)
            bug.compile(bug.get_identifier())

            # Get the diff to find the file path
            diff = PatchSet(bug.get_ground_truth())

            if bug.is_ground_truth_inverted():
                buggy_file_path = f"/bugsinpy/framework/bin/temp/{project_name}/{diff[0].target_file[2:] if diff[0].target_file.startswith('b/') else diff[0].target_file}"
            else:
                buggy_file_path = f"/bugsinpy/framework/bin/temp/{project_name}/{diff[0].source_file[2:] if diff[0].source_file.startswith('a/') else diff[0].source_file}"

            # Read the buggy file from the container
            run = subprocess.run(
                f"docker exec bugsinpy-container cat {buggy_file_path}",
                shell=True,
                capture_output=True,
                check=True,
            )
            buggy_code = run.stdout.decode("utf-8")

            # Check that buggy code exists
            if sample["buggy_code"] not in buggy_code:
                logging.error(
                    f"Could not find buggy code in {buggy_file_path} for {sample['identifier']}"
                )
                return None

            # Get the fixed and candidate code
            fixed_code = buggy_code.replace(sample["buggy_code"], sample["fixed_code"])
            candidate_code = buggy_code.replace(sample["buggy_code"], generation)

            # For BugsInPy, we can't easily test the modified code because it breaks the module structure
            # Instead, we'll just check if the code compiles and do AST matching
            # We'll set test to False for non-exact matches since we can't reliably test them

            # Check if the candidate code compiles by parsing it
            try:
                import ast

                ast.parse(candidate_code)
                result["compile"] = True
            except SyntaxError:
                result["compile"] = False

            # For BugsInPy, we can't easily run tests on modified code, so we'll set test to False
            # unless it's an exact match (which we already handled above)
            result["test"] = False

            # Check AST matching
            result["ast_match"] = self.ast_match(fixed_code, candidate_code)

            # Save the evaluation to the cache
            if self.use_cache:
                self.cache.save_to_cache_from_bug(bug, generation, result)
            return result

        except Exception as e:
            logging.error(
                f"Failed to evaluate generation for {bug.get_identifier()}: {e}"
            )
            return result

    def ast_match(self, fixed_code: str, candidate_code: str) -> bool:
        # For Python, we can use a simpler AST comparison
        try:
            import ast

            # Parse both codes into ASTs
            fixed_ast = ast.parse(fixed_code)
            candidate_ast = ast.parse(candidate_code)

            # Compare the ASTs by converting to string representation
            # This is a simplified approach - a more robust solution would
            # use a proper AST diff tool
            return ast.dump(fixed_ast) == ast.dump(candidate_ast)
        except SyntaxError:
            # If either code has syntax errors, they can't match
            return False

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
