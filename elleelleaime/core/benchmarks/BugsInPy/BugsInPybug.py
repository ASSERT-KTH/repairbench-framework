import subprocess
import shutil
import re
import os
import logging

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured BugsInPy logging output"""

    def format(self, record):
        # Extract bug info from message (format: "bug_id|command|status|error")
        message = record.getMessage()

        if "|" in message:
            parts = message.split("|", 3)
            bug_id = parts[0].strip()
            command = parts[1].strip()
            status = parts[2].strip()
            error = parts[3].strip() if len(parts) > 3 else ""

            output = f"Bug: {bug_id}\nCommand: {command}\nResult: {status}"
            if error:
                output += f"\nError: {error}"
            # output += "\n\n\n"  # 3 empty lines

            return output

        return message


# Configure logging for BugsInPy
logger = logging.getLogger("BugsInPy")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)

    # File handler - writes to bug_overview.log
    file_handler = logging.FileHandler("bug_overview.log", mode="w")
    file_handler.setLevel(logging.DEBUG)

    # Console handler - for console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Use custom formatter
    formatter = StructuredFormatter()

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


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
        version = "1" if fixed else "0"  # 1 fixed, 0 buggy

        # Remove the directory if it exists (inside the container)
        subprocess.run(
            f"docker exec bugsinpy-container rm -rf /bugsinpy/framework/bin/temp/{project_name}",
            shell=True,
            capture_output=True,
            check=False,  # Don't fail if directory doesn't exist
        )

        # Checkout the bug
        checkout_cmd = f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-checkout -p {project_name} -v {version} -i {bug_id}"

        checkout_run = subprocess.run(
            checkout_cmd,
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

        success = checkout_run.returncode == 0
        if success:
            logger.info(f"{path}|{checkout_cmd}|SUCCESS|")
        else:
            error_msg = (
                checkout_run.stderr.decode("utf-8")
                if checkout_run.stderr
                else f"Return code: {checkout_run.returncode}"
            )
            logger.error(f"{path}|{checkout_cmd}|FAILED|{error_msg}")

        return success

    def compile(self, path: str) -> CompileResult:
        project_name, bug_id = path.rsplit("-", 1)
        work_dir = f"/bugsinpy/framework/bin/temp/{project_name}"
        compile_cmd = f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-compile -w {work_dir}"

        run = subprocess.run(
            compile_cmd,
            shell=True,
            capture_output=True,
            check=False,
        )

        success = run.returncode == 0
        if success:
            logger.info(f"{path}|{compile_cmd}|SUCCESS|")
        else:
            error_msg = (
                run.stderr.decode("utf-8")
                if run.stderr
                else f"Return code: {run.returncode}"
            )
            logger.error(f"{path}|{compile_cmd}|FAILED|{error_msg}")

        return CompileResult(success)

    def test(self, path: str) -> TestResult:
        project_name, bug_id = path.rsplit("-", 1)
        work_dir = f"/bugsinpy/framework/bin/temp/{project_name}"
        test_cmd = f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-test -w {work_dir}"

        run = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            check=False,
        )

        # Decode the output and extract the last line
        stdout_lines = run.stdout.decode("utf-8").strip().splitlines()
        last_line = stdout_lines[-1] if stdout_lines else ""

        success = False
        # Check for various success indicators in pytest output
        success = run.returncode == 0

        if success:
            logger.info(f"{path}|{test_cmd}|SUCCESS|")
        else:
            error_output = last_line
            if run.stderr:
                stderr_output = run.stderr.decode("utf-8").strip()
                if stderr_output:
                    error_output = f"{error_output}\n{stderr_output}"
            logger.error(f"{path}|{test_cmd}|FAILED|{error_output}")

        return TestResult(success)

    def get_src_test_dir(self, path: str) -> str:
        project_name, bug_id = path.rsplit("-", 1)
        path = f"/bugsinpy/framework/bin/temp/{project_name}/test"

        return path

    def get_failing_tests(self) -> dict[str, str]:
        """
        Gets the failing test cases and their error messages for this bug.
        For BugsInPy, this requires running the tests to get the actual failure information.
        """
        if not hasattr(self, "_failing_tests") or self._failing_tests is None:
            self._failing_tests = self._extract_failing_tests()
        return self._failing_tests

    def _extract_failing_tests(self) -> dict[str, str]:
        """
        Extracts failing test cases by running the tests for the buggy version.
        """
        try:
            # Checkout buggy version
            self.checkout(self.get_identifier(), fixed=False)

            # Run tests to get failure information
            run = subprocess.run(
                f"docker exec bugsinpy-container /bugsinpy/framework/bin/bugsinpy-test -w /bugsinpy/framework/bin/temp/{self.project_name}",
                shell=True,
                capture_output=True,
                check=False,
            )

            # Parse the test output to extract failing tests
            stdout = run.stdout.decode("utf-8")
            stderr = run.stderr.decode("utf-8")

            failing_tests = {}

            # Look for pytest-style failures
            import re

            # Pattern to match pytest failure format
            failure_pattern = r"FAILED\s+([^\s]+)::([^\s]+)\s+-\s+(.*?)(?=\n\s*FAILED|\n\s*ERROR|\n\s*===|\Z)"
            matches = re.findall(failure_pattern, stdout + stderr, re.DOTALL)

            for test_file, test_method, error_msg in matches:
                test_name = f"{test_file}::{test_method}"
                failing_tests[test_name] = error_msg.strip()

            # If no pytest failures found, try to extract from stderr
            if not failing_tests and stderr:
                # Look for assertion errors or other test failures
                assertion_pattern = r"AssertionError:\s*(.*?)(?=\n|\Z)"
                assertion_matches = re.findall(assertion_pattern, stderr)
                if assertion_matches:
                    failing_tests["test_assertion"] = assertion_matches[0]

            return failing_tests

        except Exception as e:
            print(f"Failed to extract failing tests for {self.get_identifier()}: {e}")
            return {}
