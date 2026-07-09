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
        from elleelleaime.core.utils.python.python import extract_single_function

        return extract_single_function(bug)

    def extract_failing_test_cases(self, bug: RichBug) -> dict[str, str]:
        """
        Extracts the code of the failing test cases of a bug.
        """
        from elleelleaime.core.utils.python.python import extract_failing_test_cases

        return extract_failing_test_cases(bug)

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
