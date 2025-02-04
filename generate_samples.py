import logging
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Union

import fire
import tqdm

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.utils.jsonl import write_jsonl
from elleelleaime.sample.registry import PromptStrategyRegistry


def generate_sample(
    bug: Bug, prompt_strategy: str, **kwargs
) -> dict[str, Optional[Union[str, Bug]]]:
    """
    Generates the sample for the given bug with the given prompt strategy.
    """

    prompt_strategy_obj = PromptStrategyRegistry.get_strategy(prompt_strategy, **kwargs)
    return prompt_strategy_obj.prompt(bug)


def entry_point(
    benchmark: str,
    prompt_strategy: str,
    n_workers: int = 1,
    **kwargs,
):
    """
    Generates the test samples for the bugs of the given benchmark with the given
    prompt strategy, and writes the results to f"samples_{dataset}_{prompt_strategy}.jsonl"
    """

    # Get the benchmark, check if it exists, and initialize it
    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    # Generate the prompts in parallel
    logging.info("Building the prompts...")
    results = []

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []

        # Launch a thread for each bug
        future_to_bug = {}
        for bug in benchmark_obj.get_bugs():
            future = executor.submit(generate_sample, bug, prompt_strategy, **kwargs)
            future_to_bug[future] = bug
            futures.append(future)

        # Check that all bugs are being processed
        assert len(futures) == len(
            benchmark_obj.get_bugs()
        ), "Some bugs are not being processed"

        # Wait for the results
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            try:
                results.append(future.result())
            except Exception as e:
                logging.error(
                    f"Error while generating sample for bug {future_to_bug[future]}: {traceback.format_exc()}"
                )

    # Write results to jsonl file
    kwargs_str = "_".join([f"{key}_{value}" for key, value in kwargs.items()])
    write_jsonl(f"samples_{benchmark}_{prompt_strategy}_{kwargs_str}.jsonl", results)


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
