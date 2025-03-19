# repairbench-framework ❤️

Framework to use LLMs for automated program repair.

Supported benchmarks: 
  * Defects4J
  * GitBug-Java
  * HumanEval-Java
  * QuixBugs
  * RunBugRun

For the RepairBench patches and results, please refer to [https://github.com/ASSERT-KTH/repairbench](https://github.com/ASSERT-KTH/repairbench)

If you use this code, please cite

```bibtex
@techreport{repairbench,
  title={RepairBench: Leaderboard of Frontier Models for Program Repair}, 
  author={André Silva and Martin Monperrus},
  year={2024},
  url={https://arxiv.org/abs/2409.18952}, 
  number = {2409.18952},
  institution = {arXiv},
}
```
  
## Installation

Requires python3.11 (or latest) and python-poetry.

To setup repairbench-framework, run the following command:
```bash
./setup.sh
```
Note: By default, GitBug-Java will be installed. This benchmark is heavy (requires ~130GiB free). If you do not need to use GitBug-Java you can comment out the commands in `setup.sh` that refer to it before running the script.

## Execution

Be sure to be in the correct environment and to install the dependencies:
```bash
poetry shell
poetry install --no-root
```

Example of how to generate samples for Defects4J using the instruct strategy:
```bash
python generate_samples.py defects4j instruct
```
---

Example of how to generate patches for the samples:
```bash
python generate_patches.py samples_defects4j_instruct_.jsonl openai-chatcompletion --model-name gpt-4o-mini --n_workers 1 --num_return_sequences 10 --temperature 1.0
```
---

Example of how to evaluate the generated patches:
```bash
python evaluate_patches.py defects4j candidates_defects4j_instruct_gpt-4o-mini.jsonl.gz openai
```

Example of how to export the evaluated patches:
```bash
python export_results.py defects4j evaluation_defects4j_instruct_openai.jsonl --model_name gpt-4o-mini
```


## Development

How to run tests:
```bash
pytest -s tests/
```

How to lint your code:
```bash
black elleelleaime tests *.py
```

## Check out the results

We store all the results (prompts, patches, evaluation) in a separate repository.

Please visit https://github.com/ASSERT-KTH/repairbench for these.
