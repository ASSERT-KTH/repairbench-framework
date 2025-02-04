import shutil
import subprocess

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.compile_result import CompileResult
from elleelleaime.core.benchmarks.test_result import TestResult


class QuixBugsBug(Bug):
    """
    The class for representing QuixBugs bugs
    """

    graph_bugs = {
        "breadth_first_search",
        "depth_first_search",
        "detect_cycle",
        "minimum_spanning_tree",
        "reverse_linked_list",
        "shortest_path_length",
        "shortest_path_lengths",
        "shortest_paths",
        "topological_ordering",
    }

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
        # Copy source files
        cmd = f"cd {self.benchmark.get_path()}; mkdir {path}/java_programs; cp {'correct_java_programs' if fixed else 'java_programs'}/{self.identifier}.java {path}/java_programs/"
        run = subprocess.run(cmd, shell=True, capture_output=True, check=True)
        # Copy graph source files if bug is graph-based
        if self.identifier.lower() in self.graph_bugs:
            cmd = f"cd {self.benchmark.get_path()}; cp java_programs/Node.java {path}/java_programs/; cp java_programs/WeightedEdge.java {path}/java_programs/"
            run = subprocess.run(cmd, shell=True, capture_output=True, check=True)
        # Copy test files
        cmd = f"cd {self.benchmark.get_path()}; mkdir -p {path}/java_testcases/junit; cp java_testcases/junit/{self.identifier}_TEST.java {path}/java_testcases/junit; cp java_testcases/junit/QuixFixOracleHelper.java {path}/java_testcases/junit"
        run = subprocess.run(cmd, shell=True, capture_output=True, check=True)
        # Copy pom.xml
        cmd = f"cd {self.benchmark.get_path()}; cp pom.xml {path}/"
        run = subprocess.run(cmd, shell=True, capture_output=True, check=True)

        return run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        run = subprocess.run(
            f"cd {path}; timeout {5*60} mvn compile",
            shell=True,
            capture_output=True,
        )
        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        run = subprocess.run(
            f"cd {path}; timeout {30*60} mvn test",
            shell=True,
            capture_output=True,
        )
        return TestResult(run.returncode == 0)
