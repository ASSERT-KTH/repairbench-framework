from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.utils.benchmarks import get_benchmark
from evaluate_patches import evaluate_candidate
from generate_samples import generate_sample


class TestEvaluatePatchesInstructDefects4J:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "instruct"
    EVALUATE_STRATEGY: str = "instruct"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatchesInstructDefects4J.DEFECTS4J = get_benchmark("defects4j")
        assert TestEvaluatePatchesInstructDefects4J.DEFECTS4J is not None
        TestEvaluatePatchesInstructDefects4J.DEFECTS4J.initialize()

    @classmethod
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatchesInstructDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesInstructDefects4J.PROMPT_STRATEGY,
        )

        sample["generation"] = [
            f"```java\n{sample['fixed_code']}" + "\n// comment\n```"
        ]

        return bug, sample

    @classmethod
    def get_ast_match_sample(cls):
        bug = TestEvaluatePatchesInstructDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesInstructDefects4J.PROMPT_STRATEGY,
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

        sample["generation"] = [f"```java\n{code}\n```"]

        return bug, sample

    @classmethod
    def get_plausible_sample(cls):
        bug = TestEvaluatePatchesInstructDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesInstructDefects4J.PROMPT_STRATEGY,
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

        sample["generation"] = [f"```java\n{code}\n```"]

        return bug, sample

    @classmethod
    def get_incorrect_sample(cls):
        bug = TestEvaluatePatchesInstructDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesInstructDefects4J.PROMPT_STRATEGY,
        )
        sample["generation"] = [f"```java\n{sample['buggy_code']}\n```"]

        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatchesInstructDefects4J.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesInstructDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_ast_match_patch(self):
        bug, sample = TestEvaluatePatchesInstructDefects4J.get_ast_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesInstructDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["ast_match"] == True
        assert sample["evaluation"][0]["exact_match"] == False

    def test_incorrect_patch(self):
        bug, sample = TestEvaluatePatchesInstructDefects4J.get_incorrect_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesInstructDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False

    def test_plausible_patch(self):
        bug, sample = TestEvaluatePatchesInstructDefects4J.get_plausible_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesInstructDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False
