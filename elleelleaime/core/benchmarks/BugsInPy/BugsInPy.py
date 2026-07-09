from pathlib import Path
from typing import Optional
from io import StringIO
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.BugsInPy.BugsInPybug import BugsInPyBug
import subprocess
import logging
import re
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
        for project_name in project_names:
            run = subprocess.run(
                f"docker exec bugsinpy-container ls /bugsinpy/projects/{project_name}/bugs",
                shell=True,
                capture_output=True,
                check=True,
            )

            bugs[project_name] = set()
            for bug_id in run.stdout.split():
                try:
                    bug_id_str = bug_id.decode("utf-8").strip()
                    # Skip invalid bug IDs (files with extensions, special characters, etc.)
                    if (
                        not bug_id_str.isdigit()
                        or "." in bug_id_str
                        or "~" in bug_id_str
                        or "$" in bug_id_str
                    ):
                        logging.warning(f"Skipping invalid bug ID: {bug_id_str}")
                        continue
                    bug_id_int = int(bug_id_str)
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
                diff_path = (
                    f"/bugsinpy/projects/{project_name}/bugs/{bug_id}/bug_patch.txt"
                )
                try:
                    run = subprocess.run(
                        f"docker exec bugsinpy-container cat {diff_path}",
                        shell=True,
                        capture_output=True,
                        check=True,
                    )
                    diff = run.stdout.decode("utf-8")

                    # Skip bugs with empty ground truth
                    if not diff.strip():
                        logging.warning(
                            f"Empty ground truth for {project_name}-{bug_id}, skipping..."
                        )
                        continue

                except subprocess.CalledProcessError:
                    logging.warning(
                        f"Could not read bug_patch.txt for {project_name}-{bug_id}, skipping..."
                    )
                    continue

                self.add_bug(
                    BugsInPyBug(
                        self,
                        project_name=project_name,
                        bug_id=bug_id,
                        version_id="0",
                        ground_truth=diff,
                        failing_tests={},
                    )
                )
