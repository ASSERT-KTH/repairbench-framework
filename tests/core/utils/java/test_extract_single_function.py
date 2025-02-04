import getpass
import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from unidiff import PatchSet

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.utils.java.java import (
    extract_single_function,
    get_source_filename,
    get_target_filename,
)


class TestExtractSingleFunction:
    GITBUGJAVA: Benchmark
    DEFECTS4J: Benchmark

    @classmethod
    def setup_class(cls):
        TestExtractSingleFunction.GITBUGJAVA = get_benchmark("gitbugjava")
        assert TestExtractSingleFunction.GITBUGJAVA is not None
        TestExtractSingleFunction.GITBUGJAVA.initialize()

        TestExtractSingleFunction.DEFECTS4J = get_benchmark("defects4j")
        assert TestExtractSingleFunction.DEFECTS4J is not None
        TestExtractSingleFunction.DEFECTS4J.initialize()

    def assert_function_in_source_code(self, function: str, bug: Bug, fixed: bool):
        path = Path(
            tempfile.gettempdir(),
            f"elleelleaime-{getpass.getuser()}",
            bug.get_identifier(),
            str(uuid4()),
        )
        diff = PatchSet(bug.get_ground_truth())

        try:
            bug.checkout(str(path), fixed=fixed)
            if bug.is_ground_truth_inverted():
                buggy_file_path = Path(path, get_target_filename(diff))
                fixed_file_path = Path(path, get_source_filename(diff))
            else:
                buggy_file_path = Path(path, get_source_filename(diff))
                fixed_file_path = Path(path, get_target_filename(diff))

            if fixed:
                file_path = fixed_file_path
            else:
                file_path = buggy_file_path

            with open(file_path, "r") as file:
                source_code = file.read()
                assert function in source_code
        finally:
            shutil.rmtree(path, ignore_errors=True)

    def assert_extract(self, bug):
        assert bug is not None

        # Extract the buggy and fixed functions
        result = extract_single_function(bug)
        assert result is not None

        buggy_function, fixed_function = result
        assert buggy_function is not None
        assert fixed_function is not None

        # Assert that we can find them in the source code
        self.assert_function_in_source_code(buggy_function, bug, fixed=False)
        self.assert_function_in_source_code(fixed_function, bug, fixed=True)

    @pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
    )
    def test_mthmulders_mcs_eff905bef8d8(self):
        bug = TestExtractSingleFunction.GITBUGJAVA.get_bug(
            "mthmulders-mcs-eff905bef8d8"
        )
        self.assert_extract(bug)

    @pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
    )
    def test_semver4j_semver4j_beb7e5d466c7(self):
        bug = TestExtractSingleFunction.GITBUGJAVA.get_bug(
            "semver4j-semver4j-beb7e5d466c7"
        )
        self.assert_extract(bug)

    @pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
    )
    def test_stellar_java_stellar_sdk_1461c2fc5b89(self):
        bug = TestExtractSingleFunction.GITBUGJAVA.get_bug(
            "stellar-java-stellar-sdk-1461c2fc5b89"
        )
        self.assert_extract(bug)

    @pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
    )
    def test_traccar_traccar_d244b4bc4999(self):
        bug = TestExtractSingleFunction.GITBUGJAVA.get_bug(
            "traccar-traccar-d244b4bc4999"
        )
        self.assert_extract(bug)

    def test_lang_1(self):
        bug = TestExtractSingleFunction.DEFECTS4J.get_bug("Lang-1")
        self.assert_extract(bug)

    def test_lang_17(self):
        bug = TestExtractSingleFunction.DEFECTS4J.get_bug("Lang-17")
        self.assert_extract(bug)

    def test_chart_1(self):
        bug = TestExtractSingleFunction.DEFECTS4J.get_bug("Chart-1")
        self.assert_extract(bug)
