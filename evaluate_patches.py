import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import fire
import numpy as np
import tqdm

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.utils.jsonl import stream_jsonl, write_jsonl
from elleelleaime.evaluate.strategies.registry import PatchEvaluationStrategyRegistry


def evaluate_candidate(bug: Bug, sample: dict, strategy: str, **kwargs) -> dict:
    """
    Evaluates the candidate patch for the given sample.
    """

    evaluation_strategy = PatchEvaluationStrategyRegistry(**kwargs).get_evaluation(
        strategy
    )
    evaluation = evaluation_strategy.evaluate(bug, sample)
    sample["evaluation"] = evaluation

    return sample


def entry_point(
    benchmark: str,
    samples_path: str,
    strategy: str,
    n_workers: int = 4,
    **kwargs,
):
    """
    Evaluates the candidate patches given the samples,
    and writes the results to f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl"
    """
    # Get the benchmark, check if it exists, and initialize it
    samples_file_name = os.path.basename(samples_path)
    dir_path = os.path.dirname(samples_path)
    prompt_strategy = samples_file_name.split("_")[2].split(".")[0]
    model_name = samples_file_name.split("_")[3].split(".")[0]

    # Read the samples
    logging.info("Reading samples...")
    samples = list(stream_jsonl(samples_path))

    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        for sample in tqdm.tqdm(samples, "Lauching candidate evaluation..."):
            bug = benchmark_obj.get_bug(sample["identifier"])
            if bug is None:
                raise ValueError(f"Unknown bug {sample['identifier']}")
            futures.append(
                executor.submit(evaluate_candidate, bug, sample, strategy, **kwargs)
            )

        logging.info("Evaluating candidates...")
        results = []
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            results.append(future.result())
        samples = results

    # Write results to jsonl file
    write_jsonl(
        os.path.join(
            dir_path, f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl"
        ),
        samples,
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
