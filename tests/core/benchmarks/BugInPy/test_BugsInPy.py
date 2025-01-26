from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug

from pathlib import Path
import uuid
import shutil
import tqdm
import pytest
import getpass, tempfile
import concurrent.futures


class TestBugsInPy:
    def test_get_benchmark(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = bugs_in_py.get_bugs()

        assert bugs is not None
        assert len(bugs) == 501
        assert len(set([bug.get_identifier() for bug in bugs])) == 501
        # TODO: Check
        # assert all(bug.get_ground_truth().strip() != "" for bug in bugs)

    def checkout_bug(self, bug: Bug) -> bool:
        bug_identifier = bug.get_identifier()

        try:
            # Checkout buggy version
            bug.checkout(bug_identifier, fixed=False)

            project_name, _ = bug_identifier.rsplit("-", 1)
            path = f"./benchmarks/BugsInPy/framework/bin/temp/{project_name}"

            # Assert that there are files in the directories
            if len(list(Path(path).glob("**/*"))) == 0:
                return False
            # Assert that we can reach some Python files
            buggy_python_files = list(Path(path).glob("**/*.py"))
            if len(buggy_python_files) == 0:
                return False

            # Checkout fixed version
            bug.checkout(bug_identifier, fixed=True)
            # Assert that there are files in the directories
            if len(list(Path(path).glob("**/*"))) == 0:
                return False
            # Assert that we can reach some Python files
            buggy_python_files = list(Path(path).glob("**/*.py"))
            if len(buggy_python_files) == 0:
                return False

            return True
        finally:
            shutil.rmtree(path, ignore_errors=True)

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
        print(f"??????? Running bug {bug.get_identifier()}")

        project_name, _ = bug.get_identifier().rsplit("-", 1)
        path = f"./benchmarks/BugsInPy/framework/bin/temp/{project_name}"

        try:
            # Checkout buggy version
            bug.checkout(bug.get_identifier(), fixed=False)
            # Compile buggy version
            bug.compile(bug.get_identifier())
            # Test buggy version
            test_result = bug.test(bug.get_identifier())
            if test_result.is_passing():
                return False

            # Checkout fixed version
            bug.checkout(bug.get_identifier(), fixed=True)
            # Compile buggy version
            bug.compile(bug.get_identifier())
            # Test fixed version
            test_result = bug.test(bug.get_identifier())
            if not test_result.is_passing():
                return False

            return True
        finally:
            shutil.rmtree(path, ignore_errors=True)

    def test_run_bugs(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = list(bugs_in_py.get_bugs())
        assert bugs is not None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # TODO: Change back to 3
            for bug in bugs[:1]:  # Only run the first 3 bugs
                print(f"&&&&&& Running bug {bug.get_identifier()}")
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

    def test_get_failing_tests(self):
        bugs_in_py = get_benchmark("BugsInPy")
        assert bugs_in_py is not None
        bugs_in_py.initialize()

        bugs = bugs_in_py.get_bugs()
        assert bugs is not None

        for bug in bugs:
            failing_tests = bug.get_failing_tests()
            assert failing_tests is not None
            assert len(failing_tests) > 0
            assert all(
                failing_test.strip() != "" for failing_test in failing_tests.keys()
            )
            assert all(
                failing_test.strip() != "" for failing_test in failing_tests.values()
            )

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

                src_test_dir = bug.get_src_test_dir(path)
                assert src_test_dir is not None
                assert src_test_dir.strip() != ""
            finally:
                shutil.rmtree(path, ignore_errors=True)
