import subprocess
import shutil
import re
import os

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class Defects4JBug(RichBug):
    """
    The class for representing Defects4J bugs
    """

    def __init__(
        self,
        benchmark: Benchmark,
        pid: str,
        bid: str,
        ground_truth: str,
        failing_tests: dict[str, str],
    ) -> None:
        self.pid = pid
        self.bid = bid
        super().__init__(
            benchmark,
            f"{pid}-{bid}",
            ground_truth,
            failing_tests,
            ground_truth_inverted=True,
        )

    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)

        # Checkout the bug
        checkout_run = subprocess.run(
            f"{self.benchmark.get_bin()} checkout -p {self.pid} -v {self.bid}{'f' if fixed else 'b'} -w {path}",
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
        run = subprocess.run(
            f"cd {path} && timeout {5*60} {self.benchmark.get_bin()} compile",
            shell=True,
            capture_output=True,
            check=False,
        )
        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        # First run only relevant tests
        run = subprocess.run(
            f"cd {path} && timeout {30*60} {self.benchmark.get_bin()} test -r",
            shell=True,
            capture_output=True,
            check=False,
        )
        m = re.search(r"Failing tests: ([0-9]+)", run.stdout.decode("utf-8"))
        if not (run.returncode == 0 and m != None and int(m.group(1)) == 0):
            return TestResult(False)

        # Only run the whole test suite if the relevant tests pass
        run = subprocess.run(
            f"cd {path} && timeout {30*60} {self.benchmark.get_bin()} test",
            shell=True,
            capture_output=True,
            check=False,
        )
        m = re.search(r"Failing tests: ([0-9]+)", run.stdout.decode("utf-8"))
        return TestResult(run.returncode == 0 and m != None and int(m.group(1)) == 0)

    def get_src_test_dir(self, path: str) -> str:
        run = subprocess.run(
            f"cd {path} && {self.benchmark.get_bin()} export -p dir.src.tests",
            shell=True,
            capture_output=True,
            check=True,
        )

        return run.stdout.decode("utf-8").strip()
