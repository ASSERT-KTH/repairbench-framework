from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.utils.benchmarks import get_benchmark
from evaluate_patches import evaluate_candidate
from generate_samples import generate_sample


class TestEvaluatePatchesGoogleDefects4J:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "instruct"
    MODEL_NAME: str = "gemini-1.5-flash"
    EVALUATE_STRATEGY: str = "google"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatchesGoogleDefects4J.DEFECTS4J = get_benchmark("defects4j")
        assert TestEvaluatePatchesGoogleDefects4J.DEFECTS4J is not None
        TestEvaluatePatchesGoogleDefects4J.DEFECTS4J.initialize()

    @classmethod
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatchesGoogleDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesGoogleDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesGoogleDefects4J.MODEL_NAME,
        )

        sample["generation"] = [
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": f"```java\n{sample['fixed_code']}"
                                    + "\n// comment\n```"
                                }
                            ],
                            "role": "model",
                        },
                        "finish_reason": 1,
                        "index": 0,
                    }
                ]
            }
        ]

        return bug, sample

    @classmethod
    def get_ast_match_sample(cls):
        bug = TestEvaluatePatchesGoogleDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesGoogleDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesGoogleDefects4J.MODEL_NAME,
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

        sample["generation"] = [
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": f"```java\n{code}\n```"}],
                            "role": "model",
                        },
                        "finish_reason": 1,
                        "index": 0,
                    }
                ]
            }
        ]

        return bug, sample

    @classmethod
    def get_plausible_sample(cls):
        bug = TestEvaluatePatchesGoogleDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesGoogleDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesGoogleDefects4J.MODEL_NAME,
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

        sample["generation"] = [
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": f"```java\n{code}\n```"}],
                            "role": "model",
                        },
                        "finish_reason": 1,
                        "index": 0,
                    }
                ]
            }
        ]

        return bug, sample

    @classmethod
    def get_incorrect_sample(cls):
        bug = TestEvaluatePatchesGoogleDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesGoogleDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesGoogleDefects4J.MODEL_NAME,
        )

        sample["generation"] = [
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": f"```java\n{sample['buggy_code']}\n```"}
                            ],
                            "role": "model",
                        },
                        "finish_reason": 1,
                        "index": 0,
                    }
                ]
            }
        ]

        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatchesGoogleDefects4J.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesGoogleDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_ast_match_patch(self):
        bug, sample = TestEvaluatePatchesGoogleDefects4J.get_ast_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesGoogleDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["ast_match"] == True
        assert sample["evaluation"][0]["exact_match"] == False

    def test_incorrect_patch(self):
        bug, sample = TestEvaluatePatchesGoogleDefects4J.get_incorrect_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesGoogleDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False

    def test_plausible_patch(self):
        bug, sample = TestEvaluatePatchesGoogleDefects4J.get_plausible_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesGoogleDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False
