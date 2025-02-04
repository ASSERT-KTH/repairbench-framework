import logging
import subprocess
from pathlib import Path

from unidiff import PatchSet

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.quixbugs.quixbugsbug import QuixBugsBug


class QuixBugs(Benchmark):
    """
    The class for representing the QuixBugs benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/quixbugs").absolute()) -> None:
        super().__init__("quixbugs", path)

    def initialize(self) -> None:
        """
        Initializes the QuixBugs benchmark object by collecting all the bugs.
        """
        logging.info("Initializing QuixBugs benchmark...")

        # Find all samples
        algos = [
            x.stem
            for x in Path(self.path, "java_programs").iterdir()
            if ".java" in str(x) and x.stem.isupper()
        ]

        for algo in algos:
            buggy_file = Path(self.path, "java_programs", f"{algo}.java")
            fixed_file = Path(self.path, "correct_java_programs", f"{algo}.java")
            # Assert that the bug exists
            assert buggy_file.exists()
            assert fixed_file.exists()

            # Compute the diff
            # Note: we compute an inverted diff to be consistent with Defects4J
            run = subprocess.run(
                f"cd {self.get_path()} && diff --unified {fixed_file.relative_to(self.path)} {buggy_file.relative_to(self.path)}",
                shell=True,
                capture_output=True,
            )
            diff = PatchSet(run.stdout.decode("utf-8"))
            # Change the source file path to point to the buggy version
            diff[0].source_file = f"{buggy_file.relative_to(self.path)}"

            self.add_bug(QuixBugsBug(self, algo, str(diff)))
