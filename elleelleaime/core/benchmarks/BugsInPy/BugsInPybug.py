import subprocess
import shutil
import re
import os

from elleelleaime.core.benchmarks.benchmark import Benchmark

# TODO: Implement as `RichBug` later on
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class BugsInPyBug(RichBug):
    """
    The class for representing BugsInPy bugs
    """

    def __init__(
        self,
        benchmark: Benchmark,
        project_name: str,
        bug_id: str,
        version_id: str,  # 1 fixed, 0 buggy
        ground_truth: str,
        failing_tests: dict[str, str],
    ) -> None:
        self.project_name = project_name
        self.bug_id = bug_id
        self.version_id = version_id
        super().__init__(
            benchmark,
            f"{project_name}-{bug_id}",
            ground_truth,
            failing_tests,
            ground_truth_inverted=False,
        )

    def checkout(self, path: str, fixed: bool = False) -> bool:
        project_name, bug_id = path.rsplit("-", 1)

        # Remove the directory if it exists (inside the container)
        subprocess.run(
            f"docker exec bugsinpy-container rm -rf /bugsinpy/framework/bin/temp/{project_name}",
            shell=True,
            capture_output=True,
            check=False,  # Don't fail if directory doesn't exist
        )

        # Checkout the bug
        checkout_run = subprocess.run(
            f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-checkout -p {project_name} -v {fixed} -i {bug_id}",  # 1 fixed, 0 buggy
            shell=True,
            capture_output=True,
            check=True,
        )

        # Convert line endings to unix
        dos2unix_run = subprocess.run(
            f"docker exec bugsinpy-container find /bugsinpy/framework/bin/temp/{project_name} -type f -name '*.py' -print0 | xargs -0 -n 1 -P 4 dos2unix",
            shell=True,
            capture_output=True,
            check=False,  # Don't fail if dos2unix has issues
        )

        return checkout_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        project_name, bug_id = path.rsplit("-", 1)
        run = subprocess.run(
            f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-compile -w /bugsinpy/framework/bin/temp/{project_name}",
            shell=True,
            capture_output=True,
            check=True,
        )

        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        project_name, bug_id = path.rsplit("-", 1)

        run = subprocess.run(
            f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-test -w /bugsinpy/framework/bin/temp/{project_name}",
            shell=True,
            capture_output=True,
            check=False,
        )

        # Decode the output and extract the last line
        stdout_lines = run.stdout.decode("utf-8").strip().splitlines()
        last_line = stdout_lines[-1] if stdout_lines else ""

        success = False
        # Check for various success indicators in pytest output
        if "OK" in last_line or "passed" in last_line or "PASSED" in last_line:
            success = True

        print(f"{project_name=}")
        print(f"{bug_id=}")
        print(f"{stdout_lines=}")

        return TestResult(success)

    def get_src_test_dir(self, path: str) -> str:
        project_name, bug_id = path.rsplit("-", 1)
        path = f"/bugsinpy/framework/bin/temp/{project_name}/test"

        return path


"""
Notes:
    - youtube-dl:
        - all tests pass
    - tqdm:
        - `poetry add nose`
        - relies on `imp` module
            - not compatible with current Python version
    - tornado:
        - 10, 12, 13, 5, 6, 7, 8, 9:
            - `collections.MutableMapping` was removed from the standard collections module in Python 3.10
            - Not compatible with current Python version
        - 11, 15: backports
        - 3: buggy version works
    - thefuck:
        - relies on `imp` module
            - not compatible with current Python version
    - ansible:
        - The current project's supported Python range (>=3.10,<4.0) is not compatible with some of the required packages Python requirement:
        - ansible requires Python >=3.11, so it will not be satisfied for Python >=3.10,<3.11
"""
