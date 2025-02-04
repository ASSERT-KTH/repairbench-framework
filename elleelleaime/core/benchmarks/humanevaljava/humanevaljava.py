import logging
import subprocess
from pathlib import Path

from unidiff import PatchSet

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.humanevaljava.humanevaljavabug import HumanEvalJavaBug


class HumanEvalJava(Benchmark):
    """
    The class for representing the HumanEvalJava benchmark.
    """

    def __init__(
        self, path: Path = Path("benchmarks/human-eval-java").absolute()
    ) -> None:
        super().__init__("humanevaljava", path)

    def initialize(self) -> None:
        """
        Initializes the HumanEvalJava benchmark object by collecting all the bugs.
        """
        logging.info("Initializing HumanEvalJava benchmark...")

        # Get all samples
        locfile_path = Path(
            self.get_path(), "src", "main", "java", "humaneval", "humaneval_loc.txt"
        )
        with open(locfile_path, "r") as locfile:
            # Each line is a sample
            for line in locfile.readlines():
                # Assert that the bug exists
                bid = line.split()[0]
                assert Path(
                    self.get_path(),
                    "src",
                    "main",
                    "java",
                    "humaneval",
                    "correct",
                    f"{bid}.java",
                ).exists()
                assert Path(
                    self.get_path(),
                    "src",
                    "main",
                    "java",
                    "humaneval",
                    "buggy",
                    f"{bid}.java",
                ).exists()

                # Compute the diff
                # Note: we compute an inverted diff to be consistent with Defects4J
                # Replace the package name temporarily to generate a clean diff
                subprocess.run(
                    f"sed -i 's/package humaneval\\.correct/package humaneval\\.buggy/g' {self.get_path()}/src/main/java/humaneval/correct/{bid}.java",
                    shell=True,
                    capture_output=True,
                    check=True,
                )

                run = subprocess.run(
                    f"cd {self.get_path()} && diff --unified src/main/java/humaneval/correct/{bid}.java src/main/java/humaneval/buggy/{bid}.java",
                    shell=True,
                    capture_output=True,
                )
                diff = PatchSet(run.stdout.decode("utf-8"))
                # Change the source file path to point to the buggy version
                diff[0].source_file = f"src/main/java/humaneval/buggy/{bid}.java"

                run = subprocess.run(
                    f"sed -i 's/package humaneval\\.buggy/package humaneval\\.correct/g' {self.get_path()}/src/main/java/humaneval/correct/{bid}.java",
                    shell=True,
                    capture_output=True,
                    check=True,
                )

                self.add_bug(HumanEvalJavaBug(self, bid, str(diff)))
