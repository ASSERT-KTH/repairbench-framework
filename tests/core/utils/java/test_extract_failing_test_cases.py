import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from unidiff import PatchSet

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.utils.java.java import (
    extract_failing_test_cases,
    get_source_filename,
    get_target_filename,
)


class TestExtractFailingTestCases:
    DEFECTS4J: Benchmark

    @classmethod
    def setup_class(cls):
        TestExtractFailingTestCases.DEFECTS4J = get_benchmark("defects4j")
        assert TestExtractFailingTestCases.DEFECTS4J is not None
        TestExtractFailingTestCases.DEFECTS4J.initialize()

    def assert_extract_failing_test_cases(self, bug: RichBug):
        # Extract the failing_test_cases
        failing_test_cases = extract_failing_test_cases(bug)
        assert failing_test_cases is not None
        assert len(failing_test_cases) != 0

        # Assert that the test is the same
        for failing_test_case in failing_test_cases:
            _, method_name = failing_test_case.split("::")
            assert method_name in failing_test_cases[failing_test_case]

    def test_lang_1(self):
        bug = TestExtractFailingTestCases.DEFECTS4J.get_bug("Lang-1")
        assert bug is not None
        self.assert_extract_failing_test_cases(bug)

    def test_chart_1(self):
        bug = TestExtractFailingTestCases.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None
        self.assert_extract_failing_test_cases(bug)

    def test_closure_5(self):
        # Bug with 5 failing test cases
        bug = TestExtractFailingTestCases.DEFECTS4J.get_bug("Closure-70")
        assert bug is not None
        self.assert_extract_failing_test_cases(bug)
