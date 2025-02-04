import logging
import os
import subprocess
from io import StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
import tqdm

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.defects4j.defects4jbug import Defects4JBug


class Defects4J(Benchmark):
    """
    The class for representing the Defects4J benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/defects4j").absolute()) -> None:
        super().__init__("defects4j", path)

    def get_bin(self, options: str = "") -> Optional[str]:
        return f'{Path(self.path, "framework/bin/defects4j")}'

    def initialize(self) -> None:
        """
        Initializes the Defects4J benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing Defects4J benchmark...")

        # Get all project ids
        run = subprocess.run(
            f"{self.get_bin()} pids",
            shell=True,
            capture_output=True,
            check=True,
        )
        pids = {pid.decode("utf-8") for pid in run.stdout.split()}
        logging.info("Found %3d projects" % len(pids))

        # Get all bug ids for all pids
        bugs = {}
        for pid in tqdm.tqdm(pids):
            run = subprocess.run(
                f"{self.get_bin()} bids -p {pid}",
                shell=True,
                capture_output=True,
                check=True,
            )
            bugs[pid] = {int(bid.decode("utf-8")) for bid in run.stdout.split()}
            logging.info("Found %3d bugs for project %s" % (len(bugs[pid]), pid))

        # Initialize dataset
        for pid in pids:
            # Extract failing test and trigger cause
            run = subprocess.run(
                f"{self.get_bin()} query -p {pid} -q 'tests.trigger,tests.trigger.cause'",
                shell=True,
                capture_output=True,
                check=True,
            )
            data = run.stdout.decode("utf-8")
            df = pd.read_csv(StringIO(data), sep=",", names=["bid", "tests", "errors"])

            for bid in bugs[pid]:
                # Extract ground truth diff
                diff_path = f"benchmarks/defects4j/framework/projects/{pid}/patches/{bid}.src.patch"
                with open(diff_path, "r", encoding="ISO-8859-1") as diff_file:
                    diff = diff_file.read()

                # Extract failing test cases and trigger causes
                failing_test_cases = df[df["bid"] == bid]["tests"].values[0]
                trigger_cause = df[df["bid"] == bid]["errors"].values[0]

                failing_tests = {}
                for failing_test_case in failing_test_cases.split(";"):
                    cause = trigger_cause.split(f"{failing_test_case} --> ")[1]
                    # The trigger cause list elements are separated by ";" but sometimes this char is also included in the element itself and is not espaced
                    # To avoid this we check if there are more any remaining elements and remove them from the string.
                    if " --> " in cause:
                        while " --> " in cause:
                            cause = cause.split(" --> ")[1]
                        for test in failing_test_case.split(";"):
                            if test in cause:
                                cause = cause.replace(test, "")
                    failing_tests[failing_test_case] = cause.strip()

                self.add_bug(Defects4JBug(self, pid, bid, diff, failing_tests))
