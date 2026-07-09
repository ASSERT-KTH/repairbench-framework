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


def extract_single_function(bug: Bug) -> Optional[Tuple[str, str]]:
    """
    Extracts the buggy and fixed code of single-function bugs.
    Returns None is bug is not single-function

    Args:
        bug (Bug): The bug to extract the code from

    Returns:
        Optional[Tuple[str, str]]: None if the bug is not single-function, otherwise a tuple of the form (buggy_code, fixed_code)
    """
    buggy_path = Path(
        tempfile.gettempdir(),
        f"elleelleaime-{getpass.getuser()}",
        bug.get_identifier(),
        str(uuid4()),
    )
    fixed_path = Path(
        tempfile.gettempdir(),
        f"elleelleaime-{getpass.getuser()}",
        bug.get_identifier(),
        str(uuid4()),
    )

    try:
        # Checkout the buggy and fixed versions of the bug
        bug.checkout(str(buggy_path), fixed=False)
        bug.checkout(str(fixed_path), fixed=True)

        # Note: this diff is inverted, i.e. the target file is the buggy file
        diff = PatchSet(bug.get_ground_truth())

        if bug.is_ground_truth_inverted():
            buggy_file_path = Path(buggy_path, get_target_filename(diff))
            modified_buggy_lines = get_modified_target_lines(diff)
            fixed_file_path = Path(fixed_path, get_source_filename(diff))
            modified_fixed_lines = get_modified_source_lines(diff)
        else:
            buggy_file_path = Path(buggy_path, get_source_filename(diff))
            modified_buggy_lines = get_modified_source_lines(diff)
            fixed_file_path = Path(fixed_path, get_target_filename(diff))
            modified_fixed_lines = get_modified_target_lines(diff)

        # Run code extractor for the buggy function
        lines_args = " ".join([f"--lines {line}" for line in modified_buggy_lines])
        run = subprocess.run(
            f'docker run --rm --volume ".:/elleelleaime" --volume "{buggy_file_path.parent.absolute()}:{buggy_file_path.parent.absolute()}" --workdir "/elleelleaime"'
            + f" openjdk:11 java -jar extractor.jar -i {buggy_file_path.absolute()} {lines_args}",
            shell=True,
            capture_output=True,
        )
        if run.returncode != 0:
            buggy_code = ""
        else:
            buggy_code = run.stdout.decode("utf-8")

        # Run code extractor for the fixed function
        lines_args = " ".join([f"--lines {line}" for line in modified_fixed_lines])
        run = subprocess.run(
            f'docker run --rm --volume ".:/elleelleaime" --volume "{fixed_file_path.parent.absolute()}:{fixed_file_path.parent.absolute()}" --workdir "/elleelleaime"'
            + f" openjdk:11 java -jar extractor.jar -i {fixed_file_path.absolute()} {lines_args}",
            shell=True,
            capture_output=True,
        )
        if run.returncode != 0:
            fixed_code = ""
        else:
            fixed_code = run.stdout.decode("utf-8")

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
        # Remove the checked-out bugs
        shutil.rmtree(buggy_path, ignore_errors=True)
        shutil.rmtree(fixed_path, ignore_errors=True)


def find_test_class(path: Path, bug, class_name: str) -> Optional[Path]:
    # Get the base test directory
    base_test_dir = Path(path, bug.get_src_test_dir(str(path)))

    # Convert class name to the relative path format
    class_relative_path = f"{class_name.replace('.', '/')}.java"

    # Iterate through all the subdirectories under the base test directory
    candidates = []
    for java_file in base_test_dir.rglob("*.java"):
        # Check if the file ends with the class relative path
        if java_file.as_posix().endswith(class_relative_path):
            candidates.append(
                java_file
            )  # Return the full path to the matched Java file

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
    Extracts the code of the failing test cases of a bug.

    Args:
        bug (Bug): The bug to extract the failing test cases from

    Returns:
        dict[str, str]: A dictionary mapping failing test cases to their code
    """
    failing_test_cases = {}
    failing_tests = bug.get_failing_tests()

    for failing_test in failing_tests:
        class_name, method_name = failing_test.split("::")

        path = Path(
            tempfile.gettempdir(),
            f"elleelleaime-{getpass.getuser()}",
            bug.get_identifier(),
            str(uuid4()),
        )
        try:
            bug.checkout(str(path), fixed=False)
            test_class_path = find_test_class(path, bug, class_name)
            if test_class_path is None:
                return {}

            # Run code extractor for the failing test case
            run = subprocess.run(
                f'docker run --rm --volume ".:/elleelleaime" --volume "{test_class_path.parent.absolute()}:{test_class_path.parent.absolute()}" --workdir "/elleelleaime"'
                + f" openjdk:11 java -jar extractor.jar -i {test_class_path.absolute()} --method {method_name}",
                shell=True,
                capture_output=True,
            )
            if run.returncode == 0:
                failing_test_cases[failing_test] = run.stdout.decode("utf-8")
            else:
                return {}
        finally:
            shutil.rmtree(path, ignore_errors=True)

    return failing_test_cases


def remove_java_comments(source: str) -> Optional[str]:
    try:
        # Define states
        NORMAL, SINGLE_COMMENT, MULTI_COMMENT, STRING_LITERAL, CHAR_LITERAL = range(5)

        state = NORMAL
        result = []
        i = 0

        while i < len(source):
            # Check the current state and process accordingly
            if state == NORMAL:
                if source[i : i + 2] == "//":
                    state = SINGLE_COMMENT
                    i += 2
                elif source[i : i + 2] == "/*":
                    state = MULTI_COMMENT
                    i += 2
                elif source[i] == '"':
                    state = STRING_LITERAL
                    result.append(source[i])
                    i += 1
                elif source[i] == "'":
                    state = CHAR_LITERAL
                    result.append(source[i])
                    i += 1
                else:
                    result.append(source[i])
                    i += 1
            elif state == SINGLE_COMMENT:
                if source[i] == "\n":
                    state = NORMAL
                    result.append(source[i])
                    i += 1
                else:
                    i += 1
            elif state == MULTI_COMMENT:
                if source[i : i + 2] == "*/":
                    state = NORMAL
                    i += 2
                else:
                    i += 1
            elif state == STRING_LITERAL:
                if source[i] == "\\":
                    result.append(source[i])
                    i += 1
                    result.append(source[i])
                    i += 1
                elif source[i] == '"':
                    state = NORMAL
                    result.append(source[i])
                    i += 1
                else:
                    result.append(source[i])
                    i += 1
            elif state == CHAR_LITERAL:
                if source[i] == "\\":
                    result.append(source[i])
                    i += 1
                    result.append(source[i])
                    i += 1
                elif source[i] == "'":
                    state = NORMAL
                    result.append(source[i])
                    i += 1
                else:
                    result.append(source[i])
                    i += 1

        return "".join(result)
    except Exception as e:
        logging.warning(
            f"Failed to remove_java_comments from\n```n{source}\n```\nwith error: {e}"
        )
        return None


def remove_empty_lines(source):
    """Remove all empty lines from Java source code."""
    return re.sub(r"^\s*$\n", "", source, flags=re.MULTILINE)
