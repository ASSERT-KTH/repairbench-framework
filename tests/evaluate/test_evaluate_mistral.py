from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.utils.benchmarks import get_benchmark
from evaluate_patches import evaluate_candidate
from generate_samples import generate_sample


class TestEvaluatePatchesMistralDefects4J:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "instruct"
    MODEL_NAME: str = "codestral-2405"
    EVALUATE_STRATEGY: str = "mistral"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatchesMistralDefects4J.DEFECTS4J = get_benchmark("defects4j")
        assert TestEvaluatePatchesMistralDefects4J.DEFECTS4J is not None
        TestEvaluatePatchesMistralDefects4J.DEFECTS4J.initialize()

    @classmethod
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatchesMistralDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesMistralDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesMistralDefects4J.MODEL_NAME,
        )

        sample["generation"] = {
            "id": "5f26bfc6f38f46c2a399ef319293634a",
            "object": "chat.completion",
            "model": "codestral-2405",
            "usage": {
                "prompt_tokens": 934,
                "completion_tokens": 604,
                "total_tokens": 1538,
            },
            "created": 1732015902,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "content": f"```java\n{sample['fixed_code']}\n// comment\n```",
                        "tool_calls": None,
                        "prefix": False,
                        "role": "assistant",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatchesMistralDefects4J.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesMistralDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True
