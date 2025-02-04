from typing import Optional

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.defects4j.defects4j import Defects4J
from elleelleaime.core.benchmarks.gitbugjava.gitbugjava import GitBugJava
from elleelleaime.core.benchmarks.humanevaljava.humanevaljava import HumanEvalJava
from elleelleaime.core.benchmarks.quixbugs.quixbugs import QuixBugs

benchmarks = {
    "Defects4J": Defects4J,
    "HumanEvalJava": HumanEvalJava,
    "QuixBugs": QuixBugs,
    "GitBugJava": GitBugJava,
}


def get_benchmark(benchmark: str) -> Optional[Benchmark]:
    for b in benchmarks:
        if benchmark.lower() == b.lower():
            return benchmarks[b]()
    return None
