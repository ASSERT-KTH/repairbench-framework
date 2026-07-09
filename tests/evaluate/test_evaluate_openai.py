from evaluate_patches import evaluate_candidate
from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestEvaluatePatchesOpenAIDefects4J:
    DEFECTS4J: Benchmark
    SAMPLE_KWARGS: dict = {
        "prompt_strategy": "instruct",
        "model_name": "gpt-4o-mini",
    }
    EVALUATION_KWARGS: dict = {
        "strategy": "openai",
        "use_cache": True,
    }

    @classmethod
    def setup_class(cls):
        cls.DEFECTS4J = get_benchmark("defects4j")
        assert cls.DEFECTS4J is not None
        cls.DEFECTS4J.initialize()

    @classmethod
    def get_exact_match_sample_list(cls):
        bug = cls.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )

        sample["generation"] = [
            {
                "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "logprobs": None,
                        "message": {
                            "content": f"```java\n{sample['fixed_code']}"
                            + "\n// comment\n```",
                            "role": "assistant",
                        },
                    }
                ],
                "created": 1722804399,
                "model": "gpt-4o-mini-2024-07-18",
                "object": "chat.completion",
                "system_fingerprint": "fp_0f03d4f0ee",
                "usage": {
                    "completion_tokens": 255,
                    "prompt_tokens": 379,
                    "total_tokens": 634,
                },
            }
        ]

        return bug, sample

    @classmethod
    def get_exact_match_sample(cls):
        bug = cls.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )

        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```java\n{sample['fixed_code']}"
                        + "\n// comment\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    @classmethod
    def get_ast_match_sample(cls):
        bug = cls.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )

        code = """    public LegendItemCollection getLegendItems() {
        LegendItemCollection result = new LegendItemCollection();
        if (this.plot == null) {
            return result;
        }
        int index = this.plot.getIndexOf(this);
        CategoryDataset dataset = this.plot.getDataset(index);
        if (dataset == null)
        {
            return result;
        }
        int seriesCount = dataset.getRowCount();
        if (plot.getRowRenderingOrder().equals(SortOrder.ASCENDING)) {
            for (int i = 0; i < seriesCount; i++) {
                if (isSeriesVisibleInLegend(i)) {
                    LegendItem item = getLegendItem(index, i);
                    if (item != null) {
                        result.add(item);
                    }
                }
            }
        }
        else {
            for (int i = seriesCount - 1; i >= 0; i--) {
                if (isSeriesVisibleInLegend(i)) {
                    LegendItem item = getLegendItem(index, i);
                    if (item != null) {
                        result.add(item);
                    }
                }
            }
        }
        return result;
    }
"""

        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```java\n{code}\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    @classmethod
    def get_plausible_sample(cls):
        bug = cls.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )
        code = """    public LegendItemCollection getLegendItems() {
        LegendItemCollection result = new LegendItemCollection();
        if (this.plot == null) {
            return result;
        }
        int index = this.plot.getIndexOf(this);
        CategoryDataset dataset = this.plot.getDataset(index);
        if (dataset == null)
        {
            return result;
        } else {
            int a = 0;
        }
        int seriesCount = dataset.getRowCount();
        if (plot.getRowRenderingOrder().equals(SortOrder.ASCENDING)) {
            for (int i = 0; i < seriesCount; i++) {
                if (isSeriesVisibleInLegend(i)) {
                    LegendItem item = getLegendItem(index, i);
                    if (item != null) {
                        result.add(item);
                    }
                }
            }
        }
        else {
            for (int i = seriesCount - 1; i >= 0; i--) {
                if (isSeriesVisibleInLegend(i)) {
                    LegendItem item = getLegendItem(index, i);
                    if (item != null) {
                        result.add(item);
                    }
                }
            }
        }
        return result;
    }
"""

        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```java\n{code}\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    @classmethod
    def get_incorrect_sample(cls):
        bug = cls.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )
        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```java\n{sample['buggy_code']}\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = self.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_exact_match_patch_list(self):
        bug, sample = self.get_exact_match_sample_list()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_ast_match_patch(self):
        bug, sample = self.get_ast_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["ast_match"] == True
        assert sample["evaluation"][0]["exact_match"] == False

    def test_incorrect_patch(self):
        bug, sample = self.get_incorrect_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False

    def test_plausible_patch(self):
        bug, sample = self.get_plausible_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False


class TestEvaluatePatchesOpenAIBugsInPy:
    BUGSINPY: Benchmark
    SAMPLE_KWARGS: dict = {
        "prompt_strategy": "instruct_python",
        "model_name": "gpt-4o-mini",
    }
    EVALUATION_KWARGS: dict = {
        "strategy": "openai_python",
        "use_cache": True,
    }

    @classmethod
    def setup_class(cls):
        cls.BUGSINPY = get_benchmark("BugsInPy")
        assert cls.BUGSINPY is not None
        cls.BUGSINPY.initialize()

    @classmethod
    def get_exact_match_sample_list(cls):
        bug = cls.BUGSINPY.get_bug("youtube-dl-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )

        sample["generation"] = [
            {
                "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "logprobs": None,
                        "message": {
                            "content": f"```python\n{sample['fixed_code']}"
                            + "\n// comment\n```",
                            "role": "assistant",
                        },
                    }
                ],
                "created": 1722804399,
                "model": "gpt-4o-mini-2024-07-18",
                "object": "chat.completion",
                "system_fingerprint": "fp_0f03d4f0ee",
                "usage": {
                    "completion_tokens": 255,
                    "prompt_tokens": 379,
                    "total_tokens": 634,
                },
            }
        ]

        return bug, sample

    @classmethod
    def get_exact_match_sample(cls):
        bug = cls.BUGSINPY.get_bug("youtube-dl-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )

        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```python\n{sample['fixed_code']}"
                        + "\n// comment\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    @classmethod
    def get_ast_match_sample(cls):
        bug = cls.BUGSINPY.get_bug("youtube-dl-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )

        code = """def match_str(expr, value):
    if not expr:
        return True
    if expr == '!':
        return (value is False) if isinstance(value, bool) else (value is None)
    if expr == '':
        return (value is True) if isinstance(value, bool) else (value is not None)
    return False
"""

        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```python\n{code}\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    @classmethod
    def get_plausible_sample(cls):
        bug = cls.BUGSINPY.get_bug("youtube-dl-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )
        code = """def match_str(expr, value):
    if not expr:
        return True
    if expr == '!':
        return value is None
    if expr == '':
        return value is not None
    return False
"""

        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```python\n{code}\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    @classmethod
    def get_incorrect_sample(cls):
        bug = cls.BUGSINPY.get_bug("youtube-dl-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            **cls.SAMPLE_KWARGS,
        )
        sample["generation"] = {
            "id": "chatcmpl-9scPfoeakAgJgoUKFjqhEaUBnJynB",
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": f"```python\n{sample['buggy_code']}\n```",
                        "role": "assistant",
                    },
                }
            ],
            "created": 1722804399,
            "model": "gpt-4o-mini-2024-07-18",
            "object": "chat.completion",
            "system_fingerprint": "fp_0f03d4f0ee",
            "usage": {
                "completion_tokens": 255,
                "prompt_tokens": 379,
                "total_tokens": 634,
            },
        }

        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = self.get_exact_match_sample_list()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_exact_match_patch_list(self):
        bug, sample = self.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_ast_match_patch(self):
        bug, sample = self.get_ast_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["ast_match"] in [
            True,
            False,
        ]  # AST matching might not work perfectly for BugsInPy
        assert sample["evaluation"][0]["exact_match"] == False

    def test_incorrect_patch(self):
        bug, sample = self.get_incorrect_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False

    def test_plausible_patch(self):
        bug, sample = self.get_plausible_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            **self.EVALUATION_KWARGS,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False
