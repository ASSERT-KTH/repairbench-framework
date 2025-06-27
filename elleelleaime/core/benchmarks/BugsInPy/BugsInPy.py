from pathlib import Path
from typing import Optional
from io import StringIO
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.BugsInPy.BugsInPybug import BugsInPyBug

import subprocess
import logging

# import tqdm
import re

# import os
import pandas as pd


class BugsInPy(Benchmark):
    """
    The class for representing the BugsInPy benchmark.
    """

    def __init__(self, path: Path = Path("benchmarks/BugsInPy").absolute()) -> None:
        super().__init__("BugsInPy", path)

    def get_bin(self, options: str = "") -> Optional[str]:
        return f'{Path(self.path, "framework/bin/")}'

    def initialize(self) -> None:
        """
        Initializes the BugsInPy benchmark object by collecting the list of all projects and bugs.
        """
        logging.info("Initializing BugsInPy benchmark...")

        # Get all project names
        run = subprocess.run(
            f"docker exec bugsinpy-container ls /bugsinpy/projects",
            shell=True,
            capture_output=True,
            check=True,
        )
        project_names = {
            project_name.decode("utf-8") for project_name in run.stdout.split()
        }
        logging.info("Found %3d projects" % len(project_names))

        # Get all bug names for all project_name
        bugs = {}
        # for project_name in tqdm.tqdm(project_names):
        for project_name in project_names:
            run = subprocess.run(
                f"docker exec bugsinpy-container ls /bugsinpy/projects/{project_name}/bugs",
                shell=True,
                capture_output=True,
                check=True,
            )
            # bugs[project_name] = {
            #     int(bug_id.decode("utf-8")) for bug_id in run.stdout.split()
            # }

            bugs[project_name] = set()
            for bug_id in run.stdout.split():
                try:
                    bug_id_int = int(bug_id.decode("utf-8"))
                    bugs[project_name].add(bug_id_int)
                except ValueError:
                    logging.warning(
                        f"Skipping invalid bug ID: {bug_id.decode('utf-8')}"
                    )

            logging.info(
                "Found %3d bugs for project %s"
                % (len(bugs[project_name]), project_name)
            )

        # Initialize dataset
        for project_name in project_names:
            # Create a DataFrame to store the failing test cases and trigger causes
            df = pd.DataFrame(columns=["bid", "tests", "errors"])

            for bug_id in bugs[project_name]:
                # Extract ground truth diff
                diff_path = f"/bugsinpy/projects/{project_name}/bugs/{bug_id}/bug_patch.txt"
                # Read file content from container
                run = subprocess.run(
                    f"docker exec bugsinpy-container cat {diff_path}",
                    shell=True,
                    capture_output=True,
                    check=True,
                )
                diff = run.stdout.decode("utf-8")

                # Extract failing test cases and trigger causes
                # failing_test_cases = df[df["bug_id"] == bug_id]["tests"].values[0]
                # trigger_cause = df[df["bug_id"] == bug_id]["errors"].values[0]

                # Moved into BugsInPybug.py
                # # Checkout the bug
                # checkout_run = subprocess.run(
                #     f"docker exec -it bugsinpy-container {self.benchmark.get_bin()}bugsinpy-checkout -p {self.project_name} -v {self.version_id} -i {self.bug_id}",
                #     shell=True,
                #     capture_output=True,
                #     check=True,
                # )

                # # Compile and test the bug
                # path = f"{self.benchmark.get_bin()}/temp/{project_name}"
                # checkout_compile = subprocess.run(
                #     f"docker exec -it bugsinpy-container {self.benchmark.get_bin()}bugsinpy-compile -w {path}",
                #     shell=True,
                #     capture_output=True,
                #     check=True,
                # )

                # checkout_compile = subprocess.run(
                #     f"docker exec -it bugsinpy-container {self.benchmark.get_bin()}bugsinpy-test -w {path}",
                #     shell=True,
                #     capture_output=True,
                #     check=True,
                # )

                # # Check with default path
                # fail_path = f"{self.benchmark.get_bin()}/temp/{project_name}/bugsinpy_fail.txt"
                # with open(fail_path, "r", encoding="ISO-8859-1") as fail_file:
                #     failing_tests_content = fail_file.read()

                # # Use a regular expression to extract the test name and its context
                # pattern = r"FAIL: ([\w_.]+ \([\w_.]+\))"
                # matches = re.findall(pattern, failing_tests_content)

                # # Store the results in a dictionary if needed
                # failing_tests = {"failing_tests": matches}

                self.add_bug(
                    BugsInPyBug(
                        self,
                        project_name=project_name,
                        bug_id=bug_id,
                        version_id="0",  # 0 buggy -- is this always the case?
                        ground_truth=diff,
                        failing_tests=None,  # needs to be checked out for this?
                    )
                )
