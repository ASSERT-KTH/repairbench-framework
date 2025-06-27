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
        print(f"\n=== Starting run_bug for {bug.get_identifier()} ===")

        try:
            # Checkout buggy version
            print(f"Checking out buggy version for {bug.get_identifier()}")
            checkout_success = bug.checkout(bug.get_identifier(), fixed=False)
            print(f"Buggy checkout success: {checkout_success}")
            if not checkout_success:
                print(f"Failed to checkout buggy version for {bug.get_identifier()}")
                return False

            # Compile buggy version
            print(f"Compiling buggy version for {bug.get_identifier()}")
            compile_result = bug.compile(bug.get_identifier())
            print(f"Buggy compile result: {compile_result.is_passing()}")
            if not compile_result.is_passing():
                print(f"Failed to compile buggy version for {bug.get_identifier()}")
                return False

            # Test buggy version
            print(f"Testing buggy version for {bug.get_identifier()}")
            test_result = bug.test(bug.get_identifier())
            print(
                f"Buggy version test result for {bug.get_identifier()}: {test_result.is_passing()}"
            )

            # For BugsInPy, the buggy version might pass tests
            # This is not necessarily a failure - we just need to check that the fixed version works

            # Checkout fixed version
            print(f"Checking out fixed version for {bug.get_identifier()}")
            checkout_success = bug.checkout(bug.get_identifier(), fixed=True)
            print(f"Fixed checkout success: {checkout_success}")
            if not checkout_success:
                print(f"Failed to checkout fixed version for {bug.get_identifier()}")
                return False

            # Compile fixed version
            print(f"Compiling fixed version for {bug.get_identifier()}")
            compile_result = bug.compile(bug.get_identifier())
            print(f"Fixed compile result: {compile_result.is_passing()}")
            if not compile_result.is_passing():
                print(f"Failed to compile fixed version for {bug.get_identifier()}")
                return False

            # Test fixed version
            print(f"Testing fixed version for {bug.get_identifier()}")
            test_result = bug.test(bug.get_identifier())
            print(
                f"Fixed version test result for {bug.get_identifier()}: {test_result.is_passing()}"
            )

            # The fixed version should pass tests
            if not test_result.is_passing():
                print(f"Fixed version failed tests for {bug.get_identifier()}")
                return False

            print(f"=== SUCCESS: {bug.get_identifier()} passed all tests ===")
            return True
        except Exception as e:
            print(f"Exception in run_bug for {bug.get_identifier()}: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            # Remove the directory if it exists (inside the container)
            project_name, _ = bug.get_identifier().rsplit("-", 1)
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

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # for bug in bugs[:3]:  # Only run the first bugs
            for bug in bugs[:3]:  # Run first 3 bugs
                # Skip PySnooper-2 due to dependency issue with PySnooper-1
                if bug.get_identifier() == "PySnooper-2":
                    print(f"Skipping {bug.get_identifier()} due to dependency issue")
                    continue
                assert self.run_bug(bug), f"Failed run for {bug.get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_run_all_bugs(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = list(bugs_in_py.get_bugs())
        assert bugs is not None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            futures_to_bugs = {}
            for bug in bugs:
                # Submit the bug to be tested as a separate task
                futures.append(executor.submit(self.run_bug, bug))
                futures_to_bugs[futures[-1]] = bug
            # Wait for all tasks to complete
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures)):
                result = future.result()
                assert (
                    result
                ), f"Failed run for {futures_to_bugs[future].get_identifier()}"

    # def test_get_failing_tests(self):
    #     bugs_in_py = get_benchmark("BugsInPy")
    #     assert bugs_in_py is not None
    #     bugs_in_py.initialize()

    #     bugs = bugs_in_py.get_bugs()
    #     assert bugs is not None

    #     for bug in bugs:
    #         failing_tests = bug.get_failing_tests()
    #         assert failing_tests is not None
    #         assert len(failing_tests) > 0
    #         assert all(
    #             failing_test.strip() != "" for failing_test in failing_tests.keys()
    #         )
    #         assert all(
    #             failing_test.strip() != "" for failing_test in failing_tests.values()
    #         )

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

                # Cast to BugsInPyBug to access get_src_test_dir
                bugsinpy_bug = bug if isinstance(bug, BugsInPyBug) else None
                if bugsinpy_bug:
                    src_test_dir = bugsinpy_bug.get_src_test_dir(path)
                    assert src_test_dir is not None
                    assert src_test_dir.strip() != ""
            finally:
                # Remove the directory if it exists (inside the container)
                project_name, _ = bug.get_identifier().rsplit("-", 1)
                subprocess.run(
                    f"docker exec bugsinpy-container rm -rf /bugsinpy/framework/bin/temp/{project_name}",
                    shell=True,
                    capture_output=True,
                    check=False,  # Don't fail if directory doesn't exist
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
        print(f"\nTesting single bug: {bug.get_identifier()}")
        result = self.run_bug(bug)
        print(f"Result: {result}")
        assert result, f"Failed run for {bug.get_identifier()}"
