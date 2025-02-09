from typing import Optional, Tuple, List
from unidiff import PatchSet
from uuid import uuid4
import uuid
from pathlib import Path
import logging
import getpass, tempfile, difflib, shutil
import subprocess
import re
import ast

from elleelleaime.core.benchmarks.bug import Bug, RichBug


def extract_functions(source_code):
    # Parse the source code into an AST
    tree = ast.parse(source_code)

    # Extract all function definitions
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    # Convert the function nodes back to source code
    function_sources = [ast.get_source_segment(source_code, func) for func in functions]

    return function_sources


def extract_single_function(bug: Bug) -> Optional[Tuple[str, str]]:
    """
    Extracts the buggy and fixed code of single-function bugs.
    Returns None is bug is not single-function

    Args:
        bug (Bug): The bug to extract the code from

    Returns:
        Optional[Tuple[str, str]]: None if the bug is not single-function, otherwise a tuple of the form (buggy_code, fixed_code)
    """
    project_name, _ = bug.get_identifier().rsplit("-", 1)
    path = f"./benchmarks/BugsInPy/projects/{project_name}"

    print(f"{path=}")

    try:
        # Checkout the buggy version of the bug
        bug.checkout(bug.get_identifier(), fixed=0)
        bug.compile(bug.get_identifier())
        # Test fixed version
        # test_result = bug.test(bug.get_identifier())


        path_bin = f"./benchmarks/BugsInPy/framework/bin/temp/{project_name}"
        with open(Path(path_bin, "test", f"test_aes.py")) as f:
            buggy_code = f.read()

        buggy_functions = extract_functions(buggy_code)

        # Checkout the fixed version of the bug
        bug.checkout(bug.get_identifier(), fixed=1)
        bug.compile(bug.get_identifier())
        
        with open(Path(path_bin, "test", f"test_aes.py")) as f:
            fixed_code = f.read()

        buggy_functions = extract_functions(buggy_code)
        fixed_functions = extract_functions(fixed_code)

        assert len(buggy_functions) == len(fixed_functions)

        return buggy_code, fixed_code

    finally:
        # Remove the checked-out bugs
        # shutil.rmtree(path_bin, ignore_errors=True)
        pass
