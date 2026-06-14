from elleelleaime.core.utils.jsonl import stream_jsonl
from elleelleaime.export.token.token_calculator import TokenCalculator
from elleelleaime.core.caching.cache import Cache

from pathlib import Path
from typing import Optional

import numpy as np
import uuid
import fire
import shutil
import sys
import tqdm
import logging
import json
import os
import tempfile
import subprocess


def exact_match(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is an exact match.
    """
    return evaluation is not None and bool(evaluation["exact_match"])


def ast_match(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is an AST match.
    """
    return evaluation is not None and bool(evaluation["ast_match"])


def plausible(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is plausible.
    """
    return evaluation is not None and bool(evaluation["test"])


def compilable(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is compilable.
    """
    return evaluation is not None and bool(evaluation["compile"])


def compute_diff(buggy_code: str, fixed_code: str, context_len: int = 3) -> str:
    """
    Computes the diff between the buggy and fixed code.
    """
    buggy_path = Path(tempfile.gettempdir(), f"{uuid.uuid4()}_buggy.java")
    with open(buggy_path, "w") as f:
        f.write(buggy_code)

    fixed_path = Path(tempfile.gettempdir(), f"{uuid.uuid4()}_fixed.java")
    with open(fixed_path, "w") as f:
        f.write(fixed_code)

    # we want to ignore whitespace changes with -w which does not exist in difflib.unified_diff
    # with git diff, we even get the name of the changed function in the diff, which helps a lot
    cmd = f"git diff --patience -U{context_len} -w {buggy_path} {fixed_path}"
    run = subprocess.run(cmd, shell=True, capture_output=True)
    return run.stdout.decode("utf-8")


def pass_at_k(n: int, c: int, k: int):
    """
    :param n: total number of samples
    :param c: number of correct samples
    :param k: k in pass@$k$
    """
    if n - c < k:
        return 1.0
    else:
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


def compute_statistics(samples: list) -> dict:
    """
    Computes statistics over the evaluation.
    """
    statistics = {
        "num_bugs": 0,
        "num_bugs_with_prompt": 0,
        "num_bugs_with_patches": 0,
        "num_bugs_with_exact_match_candidates": 0,
        "num_bugs_with_ast_match_candidates": 0,
        "num_bugs_with_plausible_candidates": 0,
        "num_bugs_with_compilable_candidates": 0,
        "num_patches": 0,
        "num_compilable_patches": 0,
        "num_plausible_patches": 0,
        "num_ast_match_patches": 0,
        "num_exact_match_patches": 0,
        "bugs_with_exact_match_candidates": [],
        "bugs_with_ast_match_candidates": [],
        "bugs_with_plausible_candidates": [],
        "bugs_with_compilable_candidates": [],
    }

    for sample in tqdm.tqdm(samples, "Computing statistics..."):
        statistics["num_bugs"] += 1

        if sample["prompt"]:
            statistics["num_bugs_with_prompt"] += 1

        if "generation" in sample and sample["generation"]:
            statistics["num_bugs_with_patches"] += 1
            statistics["num_patches"] += len(sample["evaluation"])

            statistics["num_compilable_patches"] += sum(
                compilable(candidate) for candidate in sample["evaluation"]
            )
            statistics["num_plausible_patches"] += sum(
                plausible(candidate) for candidate in sample["evaluation"]
            )
            statistics["num_ast_match_patches"] += sum(
                ast_match(candidate) for candidate in sample["evaluation"]
            )
            statistics["num_exact_match_patches"] += sum(
                exact_match(candidate) for candidate in sample["evaluation"]
            )

            if any(exact_match(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_exact_match_candidates"] += 1
                statistics["bugs_with_exact_match_candidates"].append(
                    sample["identifier"]
                )
            if any(ast_match(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_ast_match_candidates"] += 1
                statistics["bugs_with_ast_match_candidates"].append(
                    sample["identifier"]
                )
            if any(compilable(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_compilable_candidates"] += 1
                statistics["bugs_with_compilable_candidates"].append(
                    sample["identifier"]
                )
            if any(plausible(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_plausible_candidates"] += 1
                statistics["bugs_with_plausible_candidates"].append(
                    sample["identifier"]
                )

    # geometric progression over k
    for k in [1, 10, 100]:
        if k < (statistics["num_patches"] // statistics["num_bugs_with_patches"]):
            statistics[f"exact_match@{k}"] = round(
                pass_at_k(
                    statistics["num_patches"],
                    statistics["num_exact_match_patches"],
                    k,
                ),
                3,
            )
            statistics[f"ast_match@{k}"] = round(
                pass_at_k(
                    statistics["num_patches"],
                    statistics["num_ast_match_patches"],
                    k,
                ),
                3,
            )
            statistics[f"plausible@{k}"] = round(
                pass_at_k(
                    statistics["num_patches"],
                    statistics["num_plausible_patches"],
                    k,
                ),
                3,
            )
            statistics[f"compilable@{k}"] = round(
                pass_at_k(
                    statistics["num_patches"],
                    statistics["num_compilable_patches"],
                    k,
                ),
                3,
            )

    statistics["bugs_with_exact_match_candidates"].sort()
    statistics["bugs_with_ast_match_candidates"].sort()
    statistics["bugs_with_plausible_candidates"].sort()
    statistics["bugs_with_compilable_candidates"].sort()

    return statistics


def compute_usage(samples: list, provider: str, model_name: str) -> Optional[dict]:
    """
    Computes the usage of the evaluation.
    """
    return TokenCalculator.compute_usage(samples, provider, model_name)


def export_patches(samples: list, dir_path: str) -> None:
    """
    Exports the patches to text files in structured directories.
    """
    # Remove the existing patches directory
    patches_dir = os.path.join(dir_path, "patches")
    if os.path.exists(patches_dir):
        shutil.rmtree(patches_dir)

    for sample in tqdm.tqdm(samples, "Exporting patches..."):
        if (
            "generation" not in sample
            or not sample["generation"]
            or all(
                candidate["generation"] is None if candidate is not None else None
                for candidate in sample["evaluation"]
            )
        ):
            continue

        # Write prompt, target diff to file
        target_diff = compute_diff(
            sample["buggy_code"],
            sample["fixed_code"],
            context_len=max(
                len(sample["buggy_code"].splitlines()),
                len(sample["fixed_code"].splitlines()),
            ),
        )

        sample_dir = os.path.join(patches_dir, sample["identifier"])
        os.makedirs(sample_dir, exist_ok=True)

        with open(os.path.join(sample_dir, "target.diff"), "w") as f:
            f.writelines(target_diff)

        with open(os.path.join(sample_dir, "prompt.txt"), "w") as f:
            f.write(sample["prompt"])

        for i, candidate in enumerate(sample["evaluation"]):
            if candidate is None or not candidate["generation"]:
                continue

            # Compute diff between generated code and buggy code
            diff = compute_diff(
                sample["buggy_code"],
                candidate["generation"],
                context_len=max(
                    len(sample["buggy_code"].splitlines()),
                    len(candidate["generation"].splitlines()),
                ),
            )

            # Store in the most restrictive sub-directory
            if exact_match(candidate):
                sub_dir = "exact_match"
            elif ast_match(candidate):
                sub_dir = "ast_match"
            elif plausible(candidate):
                sub_dir = "plausible"
            elif compilable(candidate):
                sub_dir = "compilable"
            else:
                sub_dir = "non_compilable"

            candidate_dir = os.path.join(sample_dir, sub_dir)
            os.makedirs(candidate_dir, exist_ok=True)

            with open(os.path.join(candidate_dir, f"{i}.diff"), "w") as f:
                f.writelines(diff)


def export_bugs(samples, dir_path):
    """
    Exports list of bugs considered in each category to text files.
    """
    bugs_with_prompt = sorted(
        [sample["identifier"] for sample in samples if sample["prompt"] is not None]
    )
    bugs_with_candidates = sorted(
        [
            sample["identifier"]
            for sample in samples
            if "generation" in sample
            and sample["generation"] is not None
            and len(sample["generation"]) > 0
            and not all(
                candidate["generation"] is None if candidate is not None else None
                for candidate in sample["evaluation"]
            )
        ]
    )

    with open(os.path.join(dir_path, "bugs_with_prompt.txt"), "w") as f:
        f.write("\n".join(bugs_with_prompt))

    with open(os.path.join(dir_path, "bugs_with_candidates.txt"), "w") as f:
        f.write("\n".join(bugs_with_candidates))


def export_cache(samples: list, cache_path: str, benchmark: str):
    """
    Exports the results of an evaluation file to the cache directory.
    """
    cache = Cache(cache_path)

    for sample in samples:
        if "generation" in sample and sample["generation"] is not None:
            for evaluation in sample["evaluation"]:
                if evaluation is not None and evaluation["generation"] is not None:
                    cache.save_to_cache(
                        benchmark,
                        sample["identifier"],
                        evaluation["generation"],
                        evaluation,
                    )


def entry_point(
    benchmark: str,
    samples_path: str,
    output_dir: Optional[str] = None,
    **kwargs,
):
    """
    Exports the results of an evaluation file to a structured directory.
    """
    # Get the benchmark, check if it exists, and initialize it
    samples_file_name = os.path.basename(samples_path)
    dir_path = output_dir or os.path.dirname(samples_path)
    prompt_strategy = samples_file_name.split("_")[2].split(".")[0]
    provider = samples_file_name.split("_")[3].split(".")[0]

    # Read the samples
    logging.info("Reading samples...")
    samples = list(stream_jsonl(samples_path))

    # Compute statistics for all samples
    statistics = compute_statistics(samples)
    with open(
        os.path.join(
            dir_path, f"statistics_{benchmark}_{prompt_strategy}_{provider}.json"
        ),
        "w",
    ) as f:
        json.dump(statistics, f, indent=4)

    # Compute usages for all samples
    model_name = kwargs.get("model_name", None)
    if provider:
        usage = compute_usage(samples, provider, model_name)
        if usage is not None:
            usage["provider"] = provider
            with open(
                os.path.join(
                    dir_path, f"usage_{benchmark}_{prompt_strategy}_{provider}.json"
                ),
                "w",
            ) as f:
                json.dump(usage, f, indent=4)

    # Export patches to text files in structured directories
    export_patches(samples, dir_path)
    export_bugs(samples, dir_path)

    # Export results to cache (and check for inconsistencies)
    cache_path = kwargs.get("cache_path", Path("cache"))
    export_cache(samples, cache_path, benchmark)


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
