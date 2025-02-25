from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark

import pytest
import os


class TestInfillingCodellama:
    """
    We test the generation of cloze prompts for several types of bug fixes.
    We only generate samples for bugs that are single-function and single-file.
    The bugs in parenthesis are the examples tested in this class.

    We test the following types of bug fixes:
        - Addition only
            - Single-Hunk
                - N continuous lines (Closure-5)
                - N non-continous lines (Lang-3)
                - Whole function (Chart-23)
            - Multi-Hunk
                - N hunks of addition only (Chart-4)
        - Removal only
            - Single-Hunk
                - N continuous lines (Closure-11)
                - N non-continous lines (Lang-10)
                - Whole function (no example found, other than Closure-46 which also changes the annotation)
            - Multi-Hunk
                - N hunks of removal only (Closure-115)

        - Addition and removal
            - Single-Hunk
                - N continuous lines (Chart-6)
                - N non-continuous lines (Closure-101)
            - Multi-Hunk
                - N hunks of addition and removal (Closure-4)

    Unsupported bug types:
        - non single-function, single-file (Chart-2, Math-99, Closure-46 (special case, due to annotation change!))
        - non single-function, non single-file (Chart-18)
    """

    MODEL_NAME: str = "codellama"

    # Java benchmarks
    DEFECTS4J: Benchmark
    HUMANEVALJAVA: Benchmark
    GITBUGJAVA: Benchmark
    PROMPT_STRATEGY: str = "infilling"

    # Python benchmark
    BUGSINPY: Benchmark
    PROMPT_STRATEGY_PYTHON: str = "infilling_python"

    @classmethod
    def setup_class(cls):
        # TestInfillingCodellama.DEFECTS4J = get_benchmark("defects4j")
        # assert TestInfillingCodellama.DEFECTS4J is not None
        # TestInfillingCodellama.DEFECTS4J.initialize()

        # TestInfillingCodellama.HUMANEVALJAVA = get_benchmark("humanevaljava")
        # assert TestInfillingCodellama.HUMANEVALJAVA is not None
        # TestInfillingCodellama.HUMANEVALJAVA.initialize()

        # TestInfillingCodellama.GITBUGJAVA = get_benchmark("gitbugjava")
        # assert TestInfillingCodellama.GITBUGJAVA is not None
        # TestInfillingCodellama.GITBUGJAVA.initialize()

        TestInfillingCodellama.BUGSINPY = get_benchmark("BugsInPy")
        assert TestInfillingCodellama.BUGSINPY is not None
        TestInfillingCodellama.BUGSINPY.initialize()

    def test_youtube_dl_1(self):
        bug = TestInfillingCodellama.BUGSINPY.get_bug("youtube-dl-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY_PYTHON,
            model_name=TestInfillingCodellama.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "youtube-dl-1"
        assert sample["prompt_strategy"] == "infilling_python"

        # Assert that the buggy code is properly constructed
        assert "'': lambda v: v is not None," in sample["buggy_code"]
        assert "'!': lambda v: v is None," in sample["buggy_code"]

        # Assert that the fixed code is properly constructed
        assert (
            "'': lambda v: (v is True) if isinstance(v, bool) else (v is not None),"
            in sample["fixed_code"]
        )
        assert (
            "'!': lambda v: (v is False) if isinstance(v, bool) else (v is None),"
            in sample["fixed_code"]
        )

        # Assert that the prompt is properly constructed
        assert sample["prompt"].count("<FILL_ME>") == 1


# TODO: Uncomment the following tests again

#     def test_closure_46(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-46")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-46"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert "public JSType getLeastSupertype(JSType that) {" in sample["buggy_code"]
#         assert sample["fixed_code"] == ""

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_closure_115(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-115")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-115"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert "boolean hasSideEffects = false;" in sample["buggy_code"]
#         assert "boolean hasSideEffects = false;" not in sample["fixed_code"]
#         assert (
#             "if (hasSideEffects && NodeUtil.canBeSideEffected(cArg)) {"
#             in sample["buggy_code"]
#         )
#         assert (
#             "if (hasSideEffects && NodeUtil.canBeSideEffected(cArg)) {"
#             not in sample["fixed_code"]
#         )

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith(
#                 "/**\n   * Determines whether a function can be inlined at a particular call site."
#             )
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_closure_4(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-4")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-4"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert "if (detectImplicitPrototypeCycle()) {" in sample["buggy_code"]
#         assert "if (detectImplicitPrototypeCycle()) {" not in sample["fixed_code"]
#         assert "if (detectInheritanceCycle()) {" not in sample["buggy_code"]
#         assert "if (detectInheritanceCycle()) {" in sample["fixed_code"]

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith(
#                 "/**\n   * Resolve the referenced type within the enclosing scope.\n   */"
#             )
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_chart_4(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Chart-4")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Chart-4"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert (
#             """                if (r != null) {
#                     Collection c = r.getAnnotations();"""
#             not in sample["buggy_code"]
#         )
#         assert (
#             """                if (r != null) {
#                     Collection c = r.getAnnotations();"""
#             in sample["fixed_code"]
#         )

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith("/**\n     * Returns the range for the specified axis.")
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_chart_2(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Chart-2")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Chart-2"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt was not generated
#         assert sample["prompt"] is None

#     def test_math_99(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Math-99")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Math-99"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt was not generated
#         assert sample["prompt"] is None

#     def test_chart_18(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Chart-18")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Chart-18"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt was not generated
#         assert sample["prompt"] is None

#     def test_closure_11(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-11")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-11"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert (
#             "} else if (n.getJSType() != null && parent.isAssign()) {"
#             in sample["buggy_code"]
#         )
#         assert (
#             not "} else if (n.getJSType() != null && parent.isAssign()) {"
#             in sample["fixed_code"]
#         )

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"].strip().startswith("/**\n   * Visits a GETPROP node.")
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_chart_1_keep_buggy_code(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Chart-1")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#             keep_comments=False,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Chart-1"
#         assert sample["prompt_strategy"] == "infilling"

#         assert (
#             sample["prompt"]
#             == """    public LegendItemCollection getLegendItems() {
#         LegendItemCollection result = new LegendItemCollection();
#         if (this.plot == null) {
#             return result;
#         }
#         int index = this.plot.getIndexOf(this);
#         CategoryDataset dataset = this.plot.getDataset(index);
# // buggy code
# //        if (dataset != null) {
# <FILL_ME>
#             return result;
#         }
#         int seriesCount = dataset.getRowCount();
#         if (plot.getRowRenderingOrder().equals(SortOrder.ASCENDING)) {
#             for (int i = 0; i < seriesCount; i++) {
#                 if (isSeriesVisibleInLegend(i)) {
#                     LegendItem item = getLegendItem(index, i);
#                     if (item != null) {
#                         result.add(item);
#                     }
#                 }
#             }
#         }
#         else {
#             for (int i = seriesCount - 1; i >= 0; i--) {
#                 if (isSeriesVisibleInLegend(i)) {
#                     LegendItem item = getLegendItem(index, i);
#                     if (item != null) {
#                         result.add(item);
#                     }
#                 }
#             }
#         }
#         return result;
#     }
# """
#         )

#     def test_chart_5_keep_buggy_code(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Chart-5")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#             keep_comments=False,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Chart-5"
#         assert sample["prompt_strategy"] == "infilling"

#         assert (
#             sample["prompt"]
#             == """    public XYDataItem addOrUpdate(Number x, Number y) {
#         if (x == null) {
#             throw new IllegalArgumentException("Null 'x' argument.");
#         }
# // buggy code
# //        XYDataItem overwritten = null;
# //        int index = indexOf(x);
# //        if (index >= 0 && !this.allowDuplicateXValues) {
# <FILL_ME>
#             XYDataItem existing = (XYDataItem) this.data.get(index);
#             try {
#                 overwritten = (XYDataItem) existing.clone();
#             }
#             catch (CloneNotSupportedException e) {
#                 throw new SeriesException("Couldn't clone XYDataItem!");
#             }
#             existing.setY(y);
#         }
#         else {
#             if (this.autoSort) {
#                 this.data.add(-index - 1, new XYDataItem(x, y));
#             }
#             else {
#                 this.data.add(new XYDataItem(x, y));
#             }
#             if (getItemCount() > this.maximumItemCount) {
#                 this.data.remove(0);
#             }
#         }
#         fireSeriesChanged();
#         return overwritten;
#     }
# """
#         )

#     def test_closure_11_keep_buggy_code(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-11")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#             keep_comments=False,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-11"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert (
#             "} else if (n.getJSType() != null && parent.isAssign()) {"
#             in sample["buggy_code"]
#         )
#         assert (
#             not "} else if (n.getJSType() != null && parent.isAssign()) {"
#             in sample["fixed_code"]
#         )

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith(
#                 "private void visitGetProp(NodeTraversal t, Node n, Node parent) {"
#             )
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1
#         assert "// buggy code" in sample["prompt"]
#         assert (
#             "} else if (n.getJSType() != null && parent.isAssign()) {"
#             in sample["prompt"]
#         )

#     def test_closure_2_keep_buggy_code(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-2")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#             keep_comments=False,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-2"
#         assert sample["prompt_strategy"] == "infilling"

#         assert (
#             sample["prompt"]
#             == """  private void checkInterfaceConflictProperties(NodeTraversal t, Node n,
#       String functionName, HashMap<String, ObjectType> properties,
#       HashMap<String, ObjectType> currentProperties,
#       ObjectType interfaceType) {
#     ObjectType implicitProto = interfaceType.getImplicitPrototype();
#     Set<String> currentPropertyNames;
# // buggy code
# //      currentPropertyNames = implicitProto.getOwnPropertyNames();
# <FILL_ME>
#     for (String name : currentPropertyNames) {
#       ObjectType oType = properties.get(name);
#       if (oType != null) {
#         if (!interfaceType.getPropertyType(name).isEquivalentTo(
#             oType.getPropertyType(name))) {
#           compiler.report(
#               t.makeError(n, INCOMPATIBLE_EXTENDED_PROPERTY_TYPE,
#                   functionName, name, oType.toString(),
#                   interfaceType.toString()));
#         }
#       }
#       currentProperties.put(name, interfaceType);
#     }
#     for (ObjectType iType : interfaceType.getCtorExtendedInterfaces()) {
#       checkInterfaceConflictProperties(t, n, functionName, properties,
#           currentProperties, iType);
#     }
#   }
# """
#         )

#     def test_closure_5(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-5")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-5"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert "if (gramps.isDelProp()) {" not in sample["buggy_code"]
#         assert "if (gramps.isDelProp()) {" in sample["fixed_code"]

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith(
#                 "/**\n     * Counts the number of direct (full) references to an object."
#             )
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_chart_6(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Chart-6")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Chart-6"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert "return super.equals(obj);" in sample["buggy_code"]
#         assert "return super.equals(obj);" not in sample["fixed_code"]
#         assert "ShapeList that = (ShapeList) obj;" not in sample["buggy_code"]
#         assert "ShapeList that = (ShapeList) obj;" in sample["fixed_code"]

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith(
#                 "/**\n     * Tests the list for equality with another object (typically also a list)."
#             )
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_lang_3(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Lang-3")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Lang-3"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert "if(numDecimals <= 7){" not in sample["buggy_code"]
#         assert "if(numDecimals <= 7){" in sample["fixed_code"]

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith(
#                 "/**\n     * <p>Turns a string value into a java.lang.Number.</p>\n     *"
#             )
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_closure_101(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Closure-101")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Closure-101"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert (
#             not "options.closurePass = flags.process_closure_primitives;"
#             in sample["buggy_code"]
#         )
#         assert (
#             "options.closurePass = flags.process_closure_primitives;"
#             in sample["fixed_code"]
#         )
#         assert "if (flags.process_closure_primitives) {" in sample["buggy_code"]
#         assert "if (flags.process_closure_primitives) {" not in sample["fixed_code"]

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith("@Override\n  protected CompilerOptions createOptions() {")
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_lang_10(self):
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Lang-10")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Lang-10"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the buggy code and fixed code are properly separated
#         assert "if(Character.isWhitespace(c)) {" in sample["buggy_code"]
#         assert "if(Character.isWhitespace(c)) {" not in sample["fixed_code"]
#         assert "boolean wasWhite= false;" in sample["buggy_code"]
#         assert "boolean wasWhite= false;" not in sample["fixed_code"]

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith("/**\n     * Escape constant fields into regular expression")
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_chart_7(self):
#         # This is a special case that requires latin-1 encoding
#         bug = TestInfillingCodellama.DEFECTS4J.get_bug("Chart-7")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "Chart-7"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt is properly constructed
#         assert (
#             sample["prompt"]
#             .strip()
#             .startswith(
#                 "/**\n     * Update the index values for the maximum and minimum bounds."
#             )
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_GET_ROW(self):
#         bug = TestInfillingCodellama.HUMANEVALJAVA.get_bug("GET_ROW")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "GET_ROW"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"] is not None
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_GET_ROW_keep_buggy_code(self):
#         bug = TestInfillingCodellama.HUMANEVALJAVA.get_bug("GET_ROW")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "GET_ROW"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"] is not None
#         assert "// buggy code" in sample["prompt"]
#         assert (
#             "for (int j = lst.get(0).size() - 1; j >= 0; j -= 1){" in sample["prompt"]
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_ADD(self):
#         bug = TestInfillingCodellama.HUMANEVALJAVA.get_bug("ADD")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "ADD"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"] is not None
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     def test_ADD_keep_buggy_code(self):
#         bug = TestInfillingCodellama.HUMANEVALJAVA.get_bug("ADD")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "ADD"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"] is not None
#         assert "//        return x | y;" in sample["prompt"]
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     @pytest.mark.skipif(
#         os.environ.get("CI") is not None,
#         reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
#     )
#     def test_traccar_traccar_37ed394724c0(self):
#         bug = TestInfillingCodellama.GITBUGJAVA.get_bug("traccar-traccar-37ed394724c0")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "traccar-traccar-37ed394724c0"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"] is not None
#         assert (
#             "//                    position.set(Position.KEY_BATTERY_LEVEL, buf.readUnsignedByte() * 100 / 6);"
#             in sample["prompt"]
#         )
#         assert sample["prompt"].count("<FILL_ME>") == 1

#     @pytest.mark.skipif(
#         os.environ.get("CI") is not None,
#         reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
#     )
#     def test_BrightSpots_rcv_688920f27706(self):
#         bug = TestInfillingCodellama.GITBUGJAVA.get_bug("BrightSpots-rcv-688920f27706")
#         assert bug is not None

#         sample = generate_sample(
#             bug=bug,
#             prompt_strategy=TestInfillingCodellama.PROMPT_STRATEGY,
#             model_name=TestInfillingCodellama.MODEL_NAME,
#             keep_buggy_code=True,
#         )

#         # Assert we are dealing with the correct bug and strategy
#         assert sample["identifier"] == "BrightSpots-rcv-688920f27706"
#         assert sample["prompt_strategy"] == "infilling"

#         # Assert that the prompt is properly constructed
#         assert sample["prompt"] is None
