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
            # ground_truth_inverted=True, # TODO: TypeError: Bug.__init__() got multiple values for argument 'ground_truth_inverted'
        )

    def checkout(self, path: str, fixed: bool = False) -> bool:
        project_name, bug_id = path.rsplit("-", 1)

        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)

        # Checkout the bug
        checkout_run = subprocess.run(
            f"{self.benchmark.get_bin()}/bugsinpy-checkout -p {project_name} -v {fixed} -i {bug_id}",  # 1 fixed, 0 buggy
            # f"{self.benchmark.get_bin()}/bugsinpy-checkout -p {self.project_name} -v {self.version_id} -i {self.bug_id}",
            shell=True,
            capture_output=True,
            check=True,
        )

        # Convert line endings to unix
        dos2unix_run = subprocess.run(
            f"find {path} -type f -print0 | xargs -0 -n 1 -P 4 dos2unix",
            shell=True,
            capture_output=True,
            check=True,
        )

        return checkout_run.returncode == 0 and dos2unix_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        project_name, bug_id = path.rsplit("-", 1)
        run = subprocess.run(
            f"{self.benchmark.get_bin()}/bugsinpy-compile -w {self.benchmark.get_bin()}/temp/{project_name}",
            shell=True,
            capture_output=True,
            check=True,
        )

        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        project_name, bug_id = path.rsplit("-", 1)

        run = subprocess.run(
            f"{self.benchmark.get_bin()}/bugsinpy-test -w {self.benchmark.get_bin()}/temp/{project_name}",
            shell=True,
            capture_output=True,
            check=False,
        )

        # Decode the output and extract the last line
        stdout_lines = run.stdout.decode("utf-8").strip().splitlines()
        last_line = stdout_lines[-1] if stdout_lines else ""

        if "OK" in last_line:
            success = True
        elif "FAILED" in last_line:
            success = False

        return TestResult(success)

    def get_src_test_dir(self, path: str) -> str:
        project_name, bug_id = path.rsplit("-", 1)
        path = f"{self.benchmark.get_bin()}/temp/{project_name}/test"

        return path
