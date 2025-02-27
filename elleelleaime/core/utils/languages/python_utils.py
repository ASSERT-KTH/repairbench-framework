from typing import Optional, Tuple, List
from unidiff import PatchSet
from uuid import uuid4
from pathlib import Path
import logging
import getpass, tempfile, difflib, shutil
import subprocess
import re

from elleelleaime.core.benchmarks.bug import Bug, RichBug
from elleelleaime.core.utils.language_utils import LanguageUtils


class PythonUtils(LanguageUtils):
    def get_language(self) -> str:
        return "python"

    def extract_single_function(self, bug: Bug) -> Optional[Tuple[str, str]]:
        """
        Extracts the buggy and fixed code of single-function bugs.
        Returns None is bug is not single-function

        Args:
            bug (Bug): The bug to extract the code from

        Returns:
            Optional[Tuple[str, str]]: None if the bug is not single-function, otherwise a tuple of the form (buggy_code, fixed_code)
        """
        # Get buggy and fixed path
        # TODO: Make more generic
        project_name, _ = bug.get_identifier().rsplit("-", 1)
        buggy_path = fixed_path = (
            f"./benchmarks/BugsInPy/framework/bin/temp/{project_name}"
        )

        try:
            # Buggy code
            # Checkout the buggy version of the bug
            bug.checkout(bug.get_identifier(), fixed=0)
            bug.compile(bug.get_identifier())

            # Check if the bug is inverted
            diff = PatchSet(bug.get_ground_truth())

            if bug.is_ground_truth_inverted():
                buggy_file_path = Path(buggy_path, super().get_target_filename(diff))
                modified_buggy_lines = super().get_modified_target_lines(diff)
            else:
                buggy_file_path = Path(buggy_path, super().get_source_filename(diff))
                modified_buggy_lines = super().get_modified_source_lines(diff)

            # Run code extractor for the buggy function
            def extract_code(file_path: Path, modified_lines: List[int]):
                try:
                    # Read all lines of the file
                    with file_path.open("r", encoding="utf-8") as f:
                        lines = f.readlines()

                    # Extract the modified lines
                    code = "".join(
                        lines[line - 1]
                        for line in modified_lines
                        if 0 < line <= len(lines)
                    )

                    return code.strip()

                except Exception as e:
                    print(f"Failed to extract code from {file_path} with error: {e}")
                    return ""

            buggy_code = extract_code(buggy_file_path, modified_buggy_lines)

            # Fixed code
            # Checkout the fixed version of the bug
            bug.checkout(bug.get_identifier(), fixed=1)
            bug.compile(bug.get_identifier())

            # Check if the bug is inverted
            diff = PatchSet(bug.get_ground_truth())

            if bug.is_ground_truth_inverted():
                fixed_file_path = Path(fixed_path, super().get_source_filename(diff))
                modified_fixed_lines = super().get_modified_source_lines(diff)
            else:
                fixed_file_path = Path(fixed_path, super().get_target_filename(diff))
                modified_fixed_lines = super().get_modified_target_lines(diff)

            # Run code extractor for the fixed function
            fixed_code = extract_code(fixed_file_path, modified_fixed_lines)

            # HACK: sometimes we are not able to properly retrieve the code at the function-level
            # This happens in cases suchas Closure-46 where a whole function is removed
            # To detected and circumvent such cases, we check that the function_diff is equivalent to the original diff
            # If the diffs are not equivalent, we try to fix the function diff by setting the fixed_code and buggy_code to empty
            # If on of these works we assume it as correct (since the diff is now equivalent to the original one)
            fdiff = super().compute_diff(buggy_code, fixed_code)
            if not super().assert_same_diff(
                diff, fdiff, original_inverted=bug.is_ground_truth_inverted()
            ):
                fdiff = super().compute_diff(buggy_code, "")
                if super().assert_same_diff(
                    diff, fdiff, original_inverted=bug.is_ground_truth_inverted()
                ):
                    fixed_code = ""
                else:
                    fdiff = super().compute_diff("", fixed_code)
                    if super().assert_same_diff(
                        diff, fdiff, original_inverted=bug.is_ground_truth_inverted()
                    ):
                        buggy_code = ""
                    else:
                        return None

            return buggy_code, fixed_code

        finally:
            # Remove checked-out bugs
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    def extract_failing_test_cases(self, bug: RichBug) -> dict[str, str]:
        pass

    def remove_comments(self, source: str):
        try:
            NORMAL, SINGLE_COMMENT, MULTI_COMMENT, STRING_LITERAL = range(4)
            state = NORMAL
            result = []
            i = 0

            while i < len(source):
                if state == NORMAL:
                    if source[i] == "#":
                        state = SINGLE_COMMENT
                    elif source[i : i + 3] == '"""' or source[i : i + 3] == "'''":
                        state = MULTI_COMMENT
                        i += 2
                    elif source[i] == '"' or source[i] == "'":
                        state = STRING_LITERAL
                        quote_char = source[i]
                        result.append(source[i])
                    else:
                        result.append(source[i])
                elif state == SINGLE_COMMENT:
                    if source[i] == "\n":
                        state = NORMAL
                        result.append(source[i])
                elif state == MULTI_COMMENT:
                    if source[i : i + 3] == '"""' or source[i : i + 3] == "'''":
                        state = NORMAL
                        i += 2
                elif state == STRING_LITERAL:
                    if source[i] == "\\":
                        result.append(source[i])
                        i += 1
                        result.append(source[i])
                    elif source[i] == quote_char:
                        state = NORMAL
                        result.append(source[i])
                    else:
                        result.append(source[i])

                i += 1

            return "".join(result)
        except Exception as e:
            logging.warning(
                f"Failed to remove_python_comments from\n```\n{source}\n```\nwith error: {e}"
            )
            return None
