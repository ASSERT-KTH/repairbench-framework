from typing import Optional, Tuple, List
from unidiff import PatchSet
from uuid import uuid4
from pathlib import Path
import logging
import getpass, tempfile, difflib, shutil
import subprocess
import re
import ast

from elleelleaime.core.benchmarks.bug import Bug, RichBug


def compute_diff(
    buggy_code: str, fixed_code: str, context_len: Optional[int] = None
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
    original_diff: PatchSet, function_diff: List[str], original_inverted: bool = False
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


def get_target_filename(diff: PatchSet) -> str:
    """
    Returns the target filename of the diff
    """
    return (
        diff[0].target_file[2:]
        if diff[0].target_file.startswith("b/")
        else diff[0].target_file
    )


def get_source_filename(diff: PatchSet) -> str:
    """
    Returns the source filename of the diff
    """
    return (
        diff[0].source_file[2:]
        if diff[0].source_file.startswith("a/")
        else diff[0].source_file
    )


def get_modified_source_lines(diff: PatchSet) -> List[int]:
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

    # For BugsInPy, we need to extract the entire hunk context, not just the changed lines
    if len(removed_lines) > 0:
        # Get all lines in the hunk range
        hunk_lines = []
        for hunk in diff[0]:
            hunk_lines.extend(
                range(hunk.source_start, hunk.source_start + hunk.source_length)
            )
        return hunk_lines
    else:
        # Take median value of context lines (to avoid getting lines outside the function)
        context_lines = context_lines[
            len(context_lines) // 2 : len(context_lines) // 2 + 1
        ]
        return context_lines


def get_modified_target_lines(diff: PatchSet) -> List[int]:
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

    # For BugsInPy, we need to extract the entire hunk context, not just the changed lines
    if len(added_lines) > 0:
        # Get all lines in the hunk range
        hunk_lines = []
        for hunk in diff[0]:
            hunk_lines.extend(
                range(hunk.target_start, hunk.target_start + hunk.target_length)
            )
        return hunk_lines
    else:
        # Take median value of context lines (to avoid getting lines outside the function)
        context_lines = context_lines[
            len(context_lines) // 2 : len(context_lines) // 2 + 1
        ]
        return context_lines


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
    Extracts the buggy and fixed code of single-function bugs for BugsInPy.
    Uses Docker commands to access files inside the container.

    Args:
        bug (Bug): The BugsInPy bug to extract the code from

    Returns:
        Optional[Tuple[str, str]]: None if the bug is not single-function, otherwise a tuple of the form (buggy_code, fixed_code)
    """
    project_name = bug.project_name
    bug_id = bug.bug_id
    try:
        # Buggy code
        # Checkout the buggy version of the bug
        if hasattr(bug, "checkout_fixed"):
            bug.checkout_fixed(bug.get_identifier(), fixed=False)
        else:
            bug.checkout(bug.get_identifier(), fixed=False)
        bug.compile(bug.get_identifier())

        # Check if the bug is inverted
        diff = PatchSet(bug.get_ground_truth())

        if bug.is_ground_truth_inverted():
            buggy_file_path = f"/bugsinpy/framework/bin/temp/{project_name}/{get_target_filename(diff)}"
            modified_buggy_lines = get_modified_target_lines(diff)
        else:
            buggy_file_path = f"/bugsinpy/framework/bin/temp/{project_name}/{get_source_filename(diff)}"
            modified_buggy_lines = get_modified_source_lines(diff)

        # Run code extractor for the buggy function
        def extract_code_docker(file_path: str, modified_lines: List[int]):
            try:
                # Read all lines of the file from inside the container
                run = subprocess.run(
                    f"docker exec bugsinpy-container cat {file_path}",
                    shell=True,
                    capture_output=True,
                    check=True,
                )
                lines = run.stdout.decode("utf-8").splitlines(keepends=True)

                # Extract the modified lines
                code = "".join(
                    lines[line - 1] for line in modified_lines if 0 < line <= len(lines)
                )

                return code.strip()

            except Exception as e:
                print(f"Failed to extract code from {file_path} with error: {e}")
                return ""

        buggy_code = extract_code_docker(buggy_file_path, modified_buggy_lines)

        # Fixed code
        # Checkout the fixed version of the bug
        if hasattr(bug, "checkout_fixed"):
            bug.checkout_fixed(bug.get_identifier(), fixed=True)
        else:
            bug.checkout(bug.get_identifier(), fixed=True)
        bug.compile(bug.get_identifier())

        # Check if the bug is inverted
        diff = PatchSet(bug.get_ground_truth())

        if bug.is_ground_truth_inverted():
            fixed_file_path = f"/bugsinpy/framework/bin/temp/{project_name}/{get_source_filename(diff)}"
            modified_fixed_lines = get_modified_source_lines(diff)
        else:
            fixed_file_path = f"/bugsinpy/framework/bin/temp/{project_name}/{get_target_filename(diff)}"
            modified_fixed_lines = get_modified_target_lines(diff)

        # Run code extractor for the fixed function
        fixed_code = extract_code_docker(fixed_file_path, modified_fixed_lines)

        # HACK: sometimes we are not able to properly retrieve the code at the function-level
        # This happens in cases suchas Closure-46 where a whole function is removed
        # To detected and circumvent such cases, we check that the function_diff is equivalent to the original diff
        # If the diffs are not equivalent, we try to fix the function diff by setting the fixed_code and buggy_code to empty
        # If on of these works we assume it as correct (since the diff is now equivalent to the original one)
        fdiff = compute_diff(buggy_code, fixed_code)
        if not assert_same_diff(
            diff, fdiff, original_inverted=bug.is_ground_truth_inverted()
        ):
            fdiff = compute_diff(buggy_code, "")
            if assert_same_diff(
                diff, fdiff, original_inverted=bug.is_ground_truth_inverted()
            ):
                fixed_code = ""
            else:
                fdiff = compute_diff("", fixed_code)
                if assert_same_diff(
                    diff, fdiff, original_inverted=bug.is_ground_truth_inverted()
                ):
                    buggy_code = ""
                else:
                    return None

        return buggy_code, fixed_code

    except Exception as e:
        print(
            f"Failed to extract single function for BugsInPy bug {bug.get_identifier()}: {e}"
        )
        import traceback

        traceback.print_exc()
        return None


def find_test_class(path: Path, bug, class_name: str) -> Optional[Path]:
    # Get the base test directory
    base_test_dir = Path(path, bug.get_src_test_dir(str(path)))

    # Convert class name to the relative path format
    class_relative_path = f"{class_name.replace('.', '/')}.py"

    # Iterate through all the subdirectories under the base test directory
    candidates = []
    for python_file in base_test_dir.rglob("*.py"):
        # Check if the file ends with the class relative path
        if python_file.as_posix().endswith(class_relative_path):
            candidates.append(
                python_file
            )  # Return the full path to the matched Python file

    if len(candidates) == 0:
        logging.error(f"No test class found for {class_name}")
        return None
    elif len(candidates) == 1:
        return candidates[0]
    else:
        logging.error(f"Multiple test classes found for {class_name}")
        return None


def extract_failing_test_cases(bug: RichBug) -> dict[str, str]:
    """
    Extracts the code of the failing test cases of a BugsInPy bug.
    Uses Docker commands to access files inside the container.

    Args:
        bug (Bug): The BugsInPy bug to extract the failing test cases from

    Returns:
        dict[str, str]: A dictionary mapping failing test cases to their code
    """
    project_name = bug.project_name
    bug_id = bug.bug_id
    failing_test_cases = {}

    try:
        # Checkout buggy version
        if hasattr(bug, "checkout_fixed"):
            bug.checkout_fixed(bug.get_identifier(), fixed=False)
        else:
            bug.checkout(bug.get_identifier(), fixed=False)
        bug.compile(bug.get_identifier())

        # Get failing test information
        failing_tests = bug.get_failing_tests()

        if not failing_tests:
            # Try to extract failing tests by running tests and parsing output
            failing_tests = _extract_failing_test_names_from_output(bug)

        for test_name, error_msg in failing_tests.items():
            # Parse test name (format: test_file.py::TestClass::test_method)
            if "::" in test_name:
                parts = test_name.split("::")
                if len(parts) >= 2:
                    test_file = parts[0]
                    test_method = parts[-1]  # Last part is the method name

                    # Find the test file in the container
                    test_file_path = _find_test_file_in_container(
                        project_name, test_file
                    )
                    if test_file_path:
                        # Extract the test method code
                        test_code = _extract_test_method_from_file(
                            test_file_path, test_method
                        )
                        if test_code:
                            failing_test_cases[test_name] = test_code

        return failing_test_cases

    except Exception as e:
        print(
            f"Failed to extract failing test cases for BugsInPy bug {bug.get_identifier()}: {e}"
        )
        return {}


def _extract_failing_test_names_from_output(bug: RichBug) -> dict[str, str]:
    """
    Extracts failing test names by running tests and parsing the output.
    """
    try:
        # Run tests to get failure information
        run = subprocess.run(
            f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-test -w /bugsinpy/framework/bin/temp/{bug.project_name}",
            shell=True,
            capture_output=True,
            check=False,
        )

        stdout = run.stdout.decode("utf-8")
        stderr = run.stderr.decode("utf-8")

        failing_tests = {}

        # Look for unittest-style failures
        import re

        # Pattern to match unittest failure format: test.test_utils.TestUtil.test_match_str
        failure_pattern = r"FAILED\s+([^\s]+)\.([^\s]+)\.([^\s]+)"
        matches = re.findall(failure_pattern, stdout + stderr)

        for test_file, test_class, test_method in matches:
            test_name = f"{test_file}::{test_class}::{test_method}"
            failing_tests[test_name] = "Test failed"

        return failing_tests

    except Exception as e:
        print(f"Failed to extract failing test names: {e}")
        return {}


def _find_test_file_in_container(project_name: str, test_file: str) -> Optional[str]:
    """
    Finds a test file in the BugsInPy container.
    """
    try:
        # Look for the test file in the test directory
        run = subprocess.run(
            f"docker exec bugsinpy-container find /bugsinpy/framework/bin/temp/{project_name} -name '{test_file}' -type f",
            shell=True,
            capture_output=True,
            check=True,
        )

        files = run.stdout.decode("utf-8").strip().split("\n")
        if files and files[0]:
            return files[0]

        return None

    except Exception as e:
        print(f"Failed to find test file {test_file}: {e}")
        return None


def _extract_test_method_from_file(file_path: str, method_name: str) -> Optional[str]:
    """
    Extracts a specific test method from a Python test file.
    """
    try:
        # Read the file content
        run = subprocess.run(
            f"docker exec bugsinpy-container cat {file_path}",
            shell=True,
            capture_output=True,
            check=True,
        )

        content = run.stdout.decode("utf-8")
        lines = content.splitlines()

        # Find the method definition
        method_start = None
        method_end = None
        indent_level = None

        for i, line in enumerate(lines):
            # Look for method definition
            if f"def {method_name}(" in line:
                method_start = i
                # Get the indentation level
                indent_level = len(line) - len(line.lstrip())
                continue

            # If we found the method start, look for the end
            if method_start is not None:
                # Check if this line is at the same or less indentation (end of method)
                if line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                    method_end = i
                    break

        if method_start is not None:
            if method_end is None:
                method_end = len(lines)

            # Extract the method code
            method_lines = lines[method_start:method_end]
            return "\n".join(method_lines)

        return None

    except Exception as e:
        print(f"Failed to extract test method {method_name} from {file_path}: {e}")
        return None


def remove_python_comments(source: str) -> Optional[str]:
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
        logging.warning(f"Failed to remove_python_comments with error: {e}")
        return None


def remove_empty_lines(source):
    """Remove all empty lines from the source code."""
    if source is None:
        return None
    return re.sub(r"^\s*$\n", "", source, flags=re.MULTILINE)
