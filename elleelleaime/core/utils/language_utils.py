from abc import ABC, abstractmethod

from typing import Optional, Tuple, List
from unidiff import PatchSet
from uuid import uuid4
from pathlib import Path
import logging
import getpass, tempfile, difflib, shutil
import subprocess
import re

from elleelleaime.core.benchmarks.bug import Bug, RichBug


class LanguageUtils(ABC):
    @abstractmethod
    def get_language(self) -> str:
        pass

    @abstractmethod
    def extract_single_function(self, bug: Bug) -> Optional[Tuple[str, str]]:
        pass

    @abstractmethod
    def extract_failing_test_cases(self, bug: RichBug) -> dict[str, str]:
        pass

    @abstractmethod
    def remove_comments(self, source: str):
        pass

    @staticmethod
    def get_language_utils(language: str):
        """Returns an instance of the appropriate subclass based on the language."""
        if language == "python":
            from elleelleaime.core.utils.python import PythonUtils

            return PythonUtils()
        elif language == "java":
            from elleelleaime.core.utils.java import JavaUtils

            return JavaUtils()
        else:
            raise ValueError(f"Unsupported language: '{language}'.")

    def compute_diff(
        self, buggy_code: str, fixed_code: str, context_len: Optional[int] = None
    ) -> List[str]:
        """
        Computes the diff between the buggy and fixed code.
        """
        context_len = (
            context_len
            if context_len is not None
            else max(len(buggy_code), len(fixed_code))
        )
        return list(
            difflib.unified_diff(
                buggy_code.splitlines(keepends=True),
                fixed_code.splitlines(keepends=True),
                n=context_len,
            )
        )

    def assert_same_diff(
        self,
        original_diff: PatchSet,
        function_diff: List[str],
        original_inverted: bool = False,
    ) -> bool:
        """
        Checks if the computed diff is equivalent to the original diff
        """
        original_source = ""
        original_target = ""
        original_added_lines = []
        original_removed_lines = []
        # Get the original changed lines
        for file in original_diff:
            for hunk in file:
                for line in hunk:
                    if line.is_added if original_inverted else line.is_removed:
                        original_removed_lines.append(line.value.strip())
                        original_source += line.value
                    elif line.is_removed if original_inverted else line.is_added:
                        original_added_lines.append(line.value.strip())
                        original_target += line.value
                    elif line.is_context:
                        original_source += line.value
                        original_target += line.value
        # Get the new changed lines
        new_source = ""
        new_target = ""
        new_added_lines = []
        new_removed_lines = []
        for line in function_diff:
            if any(line.startswith(x) for x in ["---", "+++", "@@"]):
                continue
            elif line.startswith("+"):
                new_added_lines.append(line[1:].strip())
                new_target += line[1:]
            elif line.startswith("-"):
                new_removed_lines.append(line[1:].strip())
                new_source += line[1:]
            else:
                new_source += line[1:]
                new_target += line[1:]
        # Check that all the lines are present in both diffs
        if (
            any([line not in original_source for line in new_removed_lines])
            or any([line not in original_target for line in new_added_lines])
            or any([line not in new_source for line in original_removed_lines])
            or any([line not in new_target for line in original_added_lines])
        ):
            return False
        return True

    def get_target_filename(self, diff: PatchSet) -> str:
        """
        Returns the target filename of the diff
        """
        return (
            diff[0].target_file[2:]
            if diff[0].target_file.startswith("b/")
            else diff[0].target_file
        )

    def get_source_filename(self, diff: PatchSet) -> str:
        """
        Returns the source filename of the diff
        """
        return (
            diff[0].source_file[2:]
            if diff[0].source_file.startswith("a/")
            else diff[0].source_file
        )

    def get_modified_source_lines(self, diff: PatchSet) -> List[int]:
        """
        Returns the line numbers of the modified source code
        """
        removed_lines = []
        context_lines = []
        for hunk in diff[0]:
            for line in hunk:
                if line.is_removed:
                    removed_lines.append(line.source_line_no)
                elif line.is_context:
                    context_lines.append(line.source_line_no)

        # Take median value of context lines (to avoid getting lines outside the function)
        context_lines = context_lines[
            len(context_lines) // 2 : len(context_lines) // 2 + 1
        ]
        return removed_lines if len(removed_lines) > 0 else context_lines

    def get_modified_target_lines(self, diff: PatchSet) -> List[int]:
        """
        Returns the line numbers of the modified target code
        """
        added_lines = []
        context_lines = []
        for hunk in diff[0]:
            for line in hunk:
                if line.is_added:
                    added_lines.append(line.target_line_no)
                elif line.is_context:
                    context_lines.append(line.target_line_no)

        # Take median value of context lines (to avoid getting lines outside the function)
        context_lines = context_lines[
            len(context_lines) // 2 : len(context_lines) // 2 + 1
        ]
        return added_lines if len(added_lines) > 0 else context_lines

    def find_test_class(self, path: Path, bug, class_name: str) -> Optional[Path]:
        # Get the base test directory
        base_test_dir = Path(path, bug.get_src_test_dir(str(path)))

        # Get the file extension
        extension = self.get_file_extension()

        # Convert class name to the relative path format
        class_relative_path = f"{class_name.replace('.', '/')}.{extension}"

        # Iterate through all the subdirectories under the base test directory
        candidates = []
        for file in base_test_dir.rglob(f"*.{extension}"):
            # Check if the file ends with the class relative path
            if file.as_posix().endswith(class_relative_path):
                candidates.append(file)  # Return the full path to the matched file

        if len(candidates) == 0:
            logging.error(f"No test class found for {class_name}")
            return None
        elif len(candidates) == 1:
            return candidates[0]
        else:
            logging.error(f"Multiple test classes found for {class_name}")
            return None

    def remove_empty_lines(self, source):
        """Remove all empty lines from the source code."""
        return re.sub(r"^\s*$\n", "", source, flags=re.MULTILINE)

    def get_file_extension(self) -> str:
        language = self.get_language()
        if language == "java":
            return ".java"
        elif language == "python":
            return ".py"
        else:
            raise ValueError(f"Unsupported language: {language}")
