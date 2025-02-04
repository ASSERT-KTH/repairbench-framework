import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import tqdm

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.gitbugjava.gitbugjavabug import GitBugJavaBug


class GitBugJava(Benchmark):
    """
    The class for representing the GitBug-Java benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/gitbug-java").absolute()) -> None:
        super().__init__("gitbugjava", path)
        self.bin = f"cd {self.path} && poetry run {path.joinpath('gitbug-java')}"

    def get_bin(self, options: str = "") -> Optional[str]:
        return self.bin

    def run_command(
        self, command: str, check: bool = True, timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        # We need to clear the VIRTUAL_ENV variable to be able to run gitbug-java commands inside its own virtualenv
        if "VIRTUAL_ENV" in env:
            env.pop("VIRTUAL_ENV")
        # The act binary should be in the path
        env["PATH"] = f"{self.path}:{self.path}/bin:{env['PATH']}"
        return subprocess.run(
            f"{self.bin} {command}",
            shell=True,
            capture_output=True,
            check=check,
            env=env,
            timeout=timeout,
        )

    def initialize(self) -> None:
        """
        Initializes the GitBug-Java benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing GitBug-Java benchmark...")

        # Get all bug ids
        run = self.run_command("bids")
        bids = {bid.decode("utf-8") for bid in run.stdout.split()}
        logging.info("Found %3d bugs" % len(bids))

        for bid in tqdm.tqdm(bids, "Loading GitBug-Java"):
            # Run info command
            run = self.run_command(
                f"info {bid}",
                check=True,
            )
            stdout = run.stdout.decode("utf-8")

            # Get diff (after "### Bug Patch", between triple ticks)
            diff = stdout.split("### Bug Patch")[1].split("```diff")[1].split("```")[0]

            # Get failing tests
            # The info command prints out the failing tests in the following format
            # - failing test
            #   - type of failure
            #   - failure message
            failing_tests = {}
            stdout = stdout.split("### Failing Tests")[1]
            for test in re.split(r"(^-)", stdout):
                # Split the three lines
                info = test.strip().split("\n")

                # Extract failing test class and method
                failing_test_case = info[0].replace("-", "", 1).strip()
                failing_test_case = (
                    failing_test_case.replace(":", "::")
                    .replace("#", "::")
                    .replace("()", "")
                )
                # Remove value between '$' and '::' if it exists (happens for jitterted tests)
                failing_test_case = re.sub(r"\$.*?::", "::", failing_test_case)

                # Extract cause
                cause = info[2].replace("-", "", 1).strip()
                if cause == "None":
                    cause = info[1].replace("-", "", 1).strip()
                failing_tests[failing_test_case] = cause

            self.add_bug(GitBugJavaBug(self, bid, diff, failing_tests))
