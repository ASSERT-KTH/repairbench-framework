from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug

from pathlib import Path
import uuid
import shutil
import tqdm
import pytest
import os, tempfile
import concurrent.futures


class TestDefects4J:
    def test_get_benchmark(self):
        defects4j = get_benchmark("defects4j")
        assert defects4j is not None
        defects4j.initialize()

        bugs = defects4j.get_bugs()

        assert bugs is not None
        assert len(bugs) == 835
        assert len(set([bug.get_identifier() for bug in bugs])) == 835
        assert all(bug.get_ground_truth().strip() != "" for bug in bugs)

    def checkout_bug(self, bug: Bug) -> bool:
        buggy_path = f"{tempfile.gettempdir()}/elleelleaime-{os.getlogin()}/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
        fixed_path = f"{tempfile.gettempdir()}/elleelleaime-{os.getlogin()}/{bug.get_identifier()}-fixed-{uuid.uuid4()}"

        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Assert that there are files in the directories
            if len(list(Path(buggy_path).glob("**/*"))) == 0:
                return False
            if len(list(Path(fixed_path).glob("**/*"))) == 0:
                return False

            # Assert that we can reach some Java files
            buggy_java_files = list(Path(buggy_path).glob("**/*.java"))
            if len(buggy_java_files) == 0:
                return False
            fixed_java_files = list(Path(fixed_path).glob("**/*.java"))
            if len(fixed_java_files) == 0:
                return False

            return True
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    def test_checkout_bugs(self):
        defects4j = get_benchmark("defects4j")
        assert defects4j is not None
        defects4j.initialize()

        # Run only the first 3 bugs to not take too long
        bugs = list(defects4j.get_bugs())[:3]
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_checkout_all_bugs(self):
        defects4j = get_benchmark("defects4j")
        assert defects4j is not None
        defects4j.initialize()

        bugs = defects4j.get_bugs()
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    def run_bug(self, bug: Bug) -> bool:
        buggy_path = f"{tempfile.gettempdir()}/elleelleaime-{os.getlogin()}/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
        fixed_path = f"{tempfile.gettempdir()}/elleelleaime-{os.getlogin()}/{bug.get_identifier()}-fixed-{uuid.uuid4()}"

        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Test buggy version
            test_result = bug.test(buggy_path)
            if test_result.is_passing():
                return False

            # Test fixed version
            test_result = bug.test(fixed_path)
            if not test_result.is_passing():
                return False

            return True
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    def test_run_bugs(self):
        defects4j = get_benchmark("defects4j")
        assert defects4j is not None
        defects4j.initialize()

        bugs = list(defects4j.get_bugs())
        assert bugs is not None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            futures_to_bugs = {}
            for bug in bugs[:3]:  # Only run the first 3 bugs
                # Submit the bug to be tested as a separate task
                futures.append(executor.submit(self.run_bug, bug))
                futures_to_bugs[futures[-1]] = bug
            # Wait for all tasks to complete
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures)):
                result = future.result()
                assert (
                    result
                ), f"Failed run for {futures_to_bugs[future].get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_run_all_bugs(self):
        defects4j = get_benchmark("defects4j")
        assert defects4j is not None
        defects4j.initialize()

        bugs = list(defects4j.get_bugs())
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