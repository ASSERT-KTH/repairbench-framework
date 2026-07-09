from evaluate_patches import evaluate_candidate
from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestEvaluatePatchesOpenRouterDefects4J:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "instruct"
    MODEL_NAME: str = "nousresearch/hermes-3-llama-3.1-405b:free"
    EVALUATE_STRATEGY: str = "openrouter"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatchesOpenRouterDefects4J.DEFECTS4J = get_benchmark("defects4j")
        assert TestEvaluatePatchesOpenRouterDefects4J.DEFECTS4J is not None
        TestEvaluatePatchesOpenRouterDefects4J.DEFECTS4J.initialize()

    @classmethod
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatchesOpenRouterDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesOpenRouterDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesOpenRouterDefects4J.MODEL_NAME,
        )

        sample["generation"] = [
            {
                "id": "gen-adIB8w6mldR8lcDnSjXOoRXhbBMf",
                "model": "nousresearch/hermes-3-llama-3.1-405b:free",
                "object": "chat.completion",
                "created": 1726481499,
                "choices": [
                    {
                        "logprobs": None,
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"```java\n{sample['fixed_code']}\n// comment\n```",
                            "refusal": "",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }
        ]

        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatchesOpenRouterDefects4J.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesOpenRouterDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True


class TestEvaluatePatchesOpenRouterBugsInPy:
    BUGSINPY: Benchmark
    PROMPT_STRATEGY: str = "instruct_python"
    MODEL_NAME: str = "nousresearch/hermes-3-llama-3.1-405b:free"
    EVALUATE_STRATEGY: str = "openrouter_python"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatchesOpenRouterBugsInPy.BUGSINPY = get_benchmark("BugsInPy")
        assert TestEvaluatePatchesOpenRouterBugsInPy.BUGSINPY is not None
        TestEvaluatePatchesOpenRouterBugsInPy.BUGSINPY.initialize()

    @classmethod
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatchesOpenRouterBugsInPy.BUGSINPY.get_bug("youtube-dl-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesOpenRouterBugsInPy.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesOpenRouterBugsInPy.MODEL_NAME,
        )

        sample["generation"] = [
            {
                "id": "gen-adIB8w6mldR8lcDnSjXOoRXhbBMf",
                "model": "nousresearch/hermes-3-llama-3.1-405b:free",
                "object": "chat.completion",
                "created": 1726481499,
                "choices": [
                    {
                        "logprobs": None,
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"```python\n{sample['fixed_code']}\n// comment\n```",
                            "refusal": "",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }
        ]

        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatchesOpenRouterBugsInPy.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesOpenRouterBugsInPy.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True
