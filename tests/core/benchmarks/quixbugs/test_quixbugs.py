from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug

from pathlib import Path
import shutil
import pytest
import uuid
import tqdm
import getpass, tempfile
import concurrent.futures


class TestQuixBugs:
    def test_get_benchmark(self):
        quixbugs = get_benchmark("quixbugs")
        assert quixbugs is not None
        quixbugs.initialize()

        bugs = quixbugs.get_bugs()

        assert bugs is not None
        assert len(bugs) == 40
        assert len(set([bug.get_identifier() for bug in bugs])) == 40

    def checkout_bug(self, bug: Bug) -> bool:
        buggy_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
        fixed_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-fixed-{uuid.uuid4()}"

        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Assert that there are files in the directories
            assert len(list(Path(buggy_path).glob("**/*"))) > 0
            assert len(list(Path(fixed_path).glob("**/*"))) > 0

            # Assert that we can reach the java file
            return (
                Path(
                    buggy_path, "java_programs", f"{bug.get_identifier()}.java"
                ).exists()
                and Path(
                    fixed_path, "java_programs", f"{bug.get_identifier()}.java"
                ).exists()
            )
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_checkout_all_bugs(self):
        quixbugs = get_benchmark("quixbugs")
        assert quixbugs is not None
        quixbugs.initialize()

        bugs = quixbugs.get_bugs()
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    def test_checkout_bugs(self):
        quixbugs = get_benchmark("quixbugs")
        assert quixbugs is not None
        quixbugs.initialize()

        # We only run 3 bugs to not take too long
        bugs = quixbugs.get_bugs()[:3]
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(bug), f"Failed checkout for {bug.get_identifier()}"

    def run_bug(self, bug: Bug) -> bool:
        buggy_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
        fixed_path = f"{tempfile.gettempdir()}/elleelleaime-{getpass.getuser()}/{bug.get_identifier()}-fixed-{uuid.uuid4()}"

        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Compile buggy version
            compile_result = bug.compile(buggy_path)
            if not compile_result.is_passing():
                return False

            # Test buggy version
            test_result = bug.test(buggy_path)
            if test_result.is_passing():
                return False

            # Compile fixed version
            compile_result = bug.compile(fixed_path)
            if not compile_result.is_passing():
                return False

            # Test fixed version
            test_result = bug.test(fixed_path)
            if not test_result.is_passing():
                return False

            return True
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_run_all_bugs(self):
        quixbugs = get_benchmark("quixbugs")
        assert quixbugs is not None
        quixbugs.initialize()

        bugs = quixbugs.get_bugs()
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
                if not result:
                    assert (
                        result
                    ), f"Failed run bug for {futures_to_bugs[future].get_identifier()}"

    def test_run_bugs(self):
        quixbugs = get_benchmark("quixbugs")
        assert quixbugs is not None
        quixbugs.initialize()

        # We only run 3 bugs to not take too long
        bugs = quixbugs.get_bugs()[:3]
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
                if not result:
                    assert (
                        result
                    ), f"Failed run bug for {futures_to_bugs[future].get_identifier()}"
