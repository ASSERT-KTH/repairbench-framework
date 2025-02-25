from typing import Optional, Tuple, List
from unidiff import PatchSet
from uuid import uuid4
from pathlib import Path
import logging
import getpass, tempfile, difflib, shutil
import subprocess
import re

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

    # Take median value of context lines (to avoid getting lines outside the function)
    context_lines = context_lines[len(context_lines) // 2 : len(context_lines) // 2 + 1]
    return removed_lines if len(removed_lines) > 0 else context_lines


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

    # Take median value of context lines (to avoid getting lines outside the function)
    context_lines = context_lines[len(context_lines) // 2 : len(context_lines) // 2 + 1]
    return added_lines if len(added_lines) > 0 else context_lines


# TODO
def extract_single_function(bug: Bug) -> Optional[Tuple[str, str]]:
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
    buggy_path = fixed_path = f"./benchmarks/BugsInPy/framework/bin/temp/{project_name}"

    try:
        # Buggy code
        # Checkout the buggy version of the bug
        bug.checkout(bug.get_identifier(), fixed=0)
        bug.compile(bug.get_identifier())

        # Check if the bug is inverted
        diff = PatchSet(bug.get_ground_truth())

        if bug.is_ground_truth_inverted():
            buggy_file_path = Path(buggy_path, get_target_filename(diff))
            modified_buggy_lines = get_modified_target_lines(diff)
        else:
            buggy_file_path = Path(buggy_path, get_source_filename(diff))
            modified_buggy_lines = get_modified_source_lines(diff)

        # Run code extractor for the buggy function
        def extract_code(file_path: Path, modified_lines: List[int]):
            try:
                # Read all lines of the file
                with file_path.open("r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Extract the modified lines
                code = "".join(
                    lines[line - 1] for line in modified_lines if 0 < line <= len(lines)
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
            fixed_file_path = Path(fixed_path, get_source_filename(diff))
            modified_fixed_lines = get_modified_source_lines(diff)
        else:
            fixed_file_path = Path(fixed_path, get_target_filename(diff))
            modified_fixed_lines = get_modified_target_lines(diff)

        # Run code extractor for the fixed function
        fixed_code = extract_code(fixed_file_path, modified_fixed_lines)

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

    finally:
        # Remove checked-out bugs
        shutil.rmtree(buggy_path, ignore_errors=True)
        shutil.rmtree(fixed_path, ignore_errors=True)


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


# TODO
def extract_failing_test_cases(bug: RichBug) -> dict[str, str]:
    return {}


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
        logging.warning(
            f"Failed to remove_python_comments from\n```\n{source}\n```\nwith error: {e}"
        )
        return None


def remove_empty_lines(source):
    """Remove all empty lines from the source code."""
    return re.sub(r"^\s*$\n", "", source, flags=re.MULTILINE)
