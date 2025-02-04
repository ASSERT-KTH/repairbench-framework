import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.benchmarks import get_benchmark


class Cache:
    def __init__(self, cache_path: str):
        self.cache_path = cache_path

    def __hash_generation(self, generation: str) -> str:
        """Hash generation to create a unique identifier for the patch"""
        return hashlib.sha256(generation.encode()).hexdigest()

    def load_from_cache(
        self, benchmark: str, bid: str, generation: str
    ) -> Optional[dict]:
        # Compute directory, check if it exists
        bug_path = Path(self.cache_path, benchmark, bid)
        if not bug_path.exists():
            return None

        # Check if the generation is cached
        generation_hash = self.__hash_generation(generation)
        if not (bug_path / generation_hash).exists():
            return None

        # Load the cached evaluation
        logging.info(f"Loading evaluation from cache for {bid}")
        with open(bug_path / generation_hash, "r") as f:
            evaluation = json.load(f)

        return evaluation

    def load_from_cache_from_bug(self, bug: Bug, generation: str) -> Optional[dict]:
        return self.load_from_cache(
            bug.benchmark.get_identifier(), bug.get_identifier(), generation
        )

    def save_to_cache(
        self, benchmark: str, bid: str, generation: str, evaluation: dict
    ):
        # Compute directory, check if it exists
        bug_path = Path(self.cache_path, benchmark, bid)
        if not bug_path.exists():
            bug_path.mkdir(parents=True)

        # Check if the evaluation already exists
        evaluation_path = bug_path / self.__hash_generation(generation)
        if evaluation_path.exists():
            with open(evaluation_path, "r") as f:
                existing_evaluation = json.load(f)
                # Check if the existing evaluation is the same as the new one
                if existing_evaluation != evaluation:
                    logging.error(
                        f"Evaluation for {bid} and generation {generation} already exists but is different. Hash: {self.__hash_generation(generation)}"
                    )
        else:
            # Save the evaluation if it does not exist
            with open(evaluation_path, "w") as f:
                json.dump(evaluation, f, indent=4)

    def save_to_cache_from_bug(self, bug: Bug, generation: str, evaluation: dict):
        self.save_to_cache(
            bug.benchmark.get_identifier(), bug.get_identifier(), generation, evaluation
        )
