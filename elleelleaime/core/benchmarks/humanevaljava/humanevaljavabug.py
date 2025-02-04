import os
import shutil
import subprocess

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.compile_result import CompileResult
from elleelleaime.core.benchmarks.test_result import TestResult


class HumanEvalJavaBug(Bug):
    """
    The class for representing HumanEvalJava bugs
    """

    def __init__(self, benchmark: Benchmark, bid: str, ground_truth: str) -> None:
        super().__init__(benchmark, bid, ground_truth, True)

    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)
        # Make the directory
        subprocess.run(
            f"mkdir -p {path}",
            shell=True,
            capture_output=True,
            check=True,
        )

        # Checkout the bug is the same as copying the entire benchmark
        checkout_run = subprocess.run(
            f"cp -r {self.benchmark.get_path()}/* {path}",
            shell=True,
            capture_output=True,
            check=True,
        )

        # If we want the fixed version, we replace the buggy program with the correct one
        # This way we can always use the same path and the same build script
        if fixed:
            shutil.copyfile(
                f"{path}/src/main/java/humaneval/correct/{self.get_identifier()}.java",
                f"{path}/src/main/java/humaneval/buggy/{self.get_identifier()}.java",
            )

            # We only needd to change the package name
            subprocess.run(
                f"sed -i 's/package humaneval\\.correct/package humaneval\\.buggy/g' {path}/src/main/java/humaneval/buggy/{self.get_identifier()}.java",
                shell=True,
                capture_output=True,
                check=True,
            )

        return checkout_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        run = subprocess.run(
            f'docker run -u {os.getuid()}:{os.getgid()} --rm --volume "{path}:{path}" --workdir "{path}" maven:3.9.8-eclipse-temurin-8 timeout {5*60} mvn compile',
            shell=True,
            capture_output=True,
        )
        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        run = subprocess.run(
            f'docker run -u {os.getuid()}:{os.getgid()} --rm --volume "{path}:{path}" --workdir "{path}" maven:3.9.8-eclipse-temurin-8 timeout {30*60} mvn test -Dtest=TEST_{self.get_identifier()}',
            shell=True,
            capture_output=True,
        )
        return TestResult(run.returncode == 0)
