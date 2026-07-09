from elleelleaime.core.benchmarks import bug
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.BugsInPy.BugsInPybug import BugsInPyBug

from pathlib import Path
import uuid
import shutil
import tqdm
import pytest
import getpass, tempfile
import concurrent.futures
import subprocess
import logging

# Get logger for test execution
test_logger = logging.getLogger("BugsInPy.test")


class TestBugsInPy:
    def test_get_benchmark(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()
        bugs = bugs_in_py.get_bugs()
        assert bugs is not None
        assert len(bugs) == 500
        assert len(set([bug.get_identifier() for bug in bugs])) == 500
        assert all(bug.get_ground_truth().strip() != "" for bug in bugs)

    def checkout_bug(self, bug: Bug) -> bool:
        bug_identifier = bug.get_identifier()

        try:
            # Checkout buggy version
            bug.checkout(bug_identifier, fixed=False)

            project_name, _ = bug_identifier.rsplit("-", 1)

            # Check files inside the Docker container
            result = subprocess.run(
                f"docker exec bugsinpy-container find /bugsinpy/framework/bin/temp/{project_name} -type f | wc -l",
                shell=True,
                capture_output=True,
                check=True,
            )
            file_count = int(result.stdout.decode("utf-8").strip())
            if file_count == 0:
                return False

            # Check for Python files inside the container
            result = subprocess.run(
                f"docker exec bugsinpy-container find /bugsinpy/framework/bin/temp/{project_name} -name '*.py' | wc -l",
                shell=True,
                capture_output=True,
                check=True,
            )
            python_file_count = int(result.stdout.decode("utf-8").strip())
            if python_file_count == 0:
                return False

            # Checkout fixed version
            bug.checkout(bug_identifier, fixed=True)

            # Check files inside the Docker container again
            result = subprocess.run(
                f"docker exec bugsinpy-container find /bugsinpy/framework/bin/temp/{project_name} -type f | wc -l",
                shell=True,
                capture_output=True,
                check=True,
            )
            file_count = int(result.stdout.decode("utf-8").strip())
            if file_count == 0:
                return False

            # Check for Python files inside the container again
            result = subprocess.run(
                f"docker exec bugsinpy-container find /bugsinpy/framework/bin/temp/{project_name} -name '*.py' | wc -l",
                shell=True,
                capture_output=True,
                check=True,
            )
            python_file_count = int(result.stdout.decode("utf-8").strip())
            if python_file_count == 0:
                return False

            return True
        finally:
            # Remove the directory if it exists (inside the container)
            project_name, _ = bug_identifier.rsplit("-", 1)
            subprocess.run(
                f"docker exec bugsinpy-container rm -rf /bugsinpy/framework/bin/temp/{project_name}",
                shell=True,
                capture_output=True,
                check=False,  # Don't fail if directory doesn't exist
            )

    def test_checkout_bugs(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        # Run only the first 3 bugs to not take too long
        bugs = list(bugs_in_py.get_bugs())[:3]
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_checkout_all_bugs(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = bugs_in_py.get_bugs()
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    def run_bug(self, bug: Bug) -> bool:
        project_name, _ = bug.get_identifier().rsplit("-", 1)
        bug_id = bug.get_identifier()

        try:
            test_logger.info(f"[{bug_id}] Starting bug test")

            # Checkout buggy version
            test_logger.debug(f"[{bug_id}] Checking out buggy version")
            checkout_success = bug.checkout(bug_id, fixed=False)
            if not checkout_success:
                test_logger.error(f"[{bug_id}] FAILED at: checkout buggy version")
                return False

            # Compile buggy version
            test_logger.debug(f"[{bug_id}] Compiling buggy version")
            compile_result = bug.compile(bug_id)
            if not compile_result.is_passing():
                test_logger.error(f"[{bug_id}] FAILED at: compile buggy version")
                return False

            # Test buggy version
            test_logger.debug(f"[{bug_id}] Testing buggy version")
            test_result = bug.test(bug_id)

            # Checkout fixed version
            test_logger.debug(f"[{bug_id}] Checking out fixed version")
            checkout_success = bug.checkout(bug_id, fixed=True)
            if not checkout_success:
                test_logger.error(f"[{bug_id}] FAILED at: checkout fixed version")
                return False

            # Compile fixed version
            test_logger.debug(f"[{bug_id}] Compiling fixed version")
            compile_result = bug.compile(bug_id)
            if not compile_result.is_passing():
                test_logger.error(f"[{bug_id}] FAILED at: compile fixed version")
                return False

            # Test fixed version
            test_logger.debug(f"[{bug_id}] Testing fixed version")
            test_result = bug.test(bug_id)

            # The fixed version should pass tests
            if not test_result.is_passing():
                test_logger.error(
                    f"[{bug_id}] FAILED at: test fixed version (fixed version should pass)"
                )
                return False

            test_logger.info(f"[{bug_id}] PASSED all stages")
            return True
        except Exception as e:
            test_logger.error(f"[{bug_id}] Exception: {e}")
            import traceback

            test_logger.error(f"[{bug_id}] Traceback:\n{traceback.format_exc()}")
            return False
        finally:
            # Remove the directory if it exists (inside the container)
            project_name, _ = bug_id.rsplit("-", 1)
            subprocess.run(
                f"docker exec bugsinpy-container rm -rf /bugsinpy/framework/bin/temp/{project_name}",
                shell=True,
                capture_output=True,
                check=False,  # Don't fail if directory doesn't exist
            )

    def test_run_bugs(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = list(bugs_in_py.get_bugs())
        assert bugs is not None

        for bug in bugs[:3]:  # Run first 3 bugs
            # if bug.get_identifier() == "PySnooper-2":
            #     continue
            assert self.run_bug(bug), f"Failed run for {bug.get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_run_all_bugs(self):
        test_logger.info("=" * 80)
        test_logger.info("Starting BugsInPy test run for all bugs")
        test_logger.info("=" * 80)

        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = list(bugs_in_py.get_bugs())
        assert bugs is not None

        passed_bugs = []
        failed_bugs = []

        for bug in bugs:
            # if not bug.get_identifier() == "cookiecutter-1":
            #     continue
            test_logger.info("\n")
            test_logger.info(f"Bug: {bug.get_identifier()}")
            result = self.run_bug(bug)

            if result is False:
                test_logger.info(f"Failed run for\t{bug.get_identifier()}")
                failed_bugs.append(bug.get_identifier())
            elif result is True:
                test_logger.info(f"Success run for\t{bug.get_identifier()}")
                passed_bugs.append(bug.get_identifier())

        # Log summary
        test_logger.info("=" * 80)
        test_logger.info(
            f"Test Summary: {len(passed_bugs)} passed, {len(failed_bugs)} failed"
        )
        test_logger.info(f"Total bugs tested: {len(passed_bugs) + len(failed_bugs)}")
        if failed_bugs:
            test_logger.info(f"Failed bugs: {', '.join(failed_bugs)}")
        test_logger.info("=" * 80)
        test_logger.info("Test run completed.")

    def test_get_failing_tests(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = bugs_in_py.get_bugs()
        assert bugs is not None

        # Limit scope to a few bugs to keep runtime reasonable
        for bug in list(bugs)[:5]:
            failing_tests = bug.get_failing_tests()
            assert isinstance(failing_tests, dict)
            for test_name, error_msg in failing_tests.items():
                assert isinstance(test_name, str) and test_name.strip() != ""
                assert isinstance(error_msg, str) and error_msg.strip() != ""

    def test_get_src_test_dir(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = bugs_in_py.get_bugs()
        assert bugs is not None

        # Run only on the first 3 bugs to not take too long
        bugs = list(bugs_in_py.get_bugs())[:3]
        assert bugs is not None

        for bug in bugs:
            try:
                path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-{uuid.uuid4()}"
                bug.checkout(path, fixed=False)

                bugsinpy_bug = bug if isinstance(bug, BugsInPyBug) else None
                if bugsinpy_bug:
                    src_test_dir = bugsinpy_bug.get_src_test_dir(path)
                    assert src_test_dir is not None
                    assert src_test_dir.strip() != ""
            finally:
                project_name, _ = bug.get_identifier().rsplit("-", 1)
                subprocess.run(
                    f"docker exec bugsinpy-container rm -rf /bugsinpy/framework/bin/temp/{project_name}",
                    shell=True,
                    capture_output=True,
                    check=False,
                )

    def test_run_single_bug(self):
        """Test a single bug to see detailed output"""
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = list(bugs_in_py.get_bugs())
        assert bugs is not None

        # Test just the first bug
        bug = bugs[0]
        result = self.run_bug(bug)
        assert result, f"Failed run for {bug.get_identifier()}"
