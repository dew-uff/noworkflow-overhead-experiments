"""paper_tables.py reproduces the tables of the submitted paper from the evaluation of 2.1.3.

    python3 -m pytest test_paper_tables.py

The expected rows are those of Tables 5 to 8 of the submitted paper (`main.tex` at the
submission, 2026-09-29), copied verbatim, so that the medians, the rounding, the shading, the
markers, the average ranks and the effect sizes are shown to be the same arithmetic as the
paper's, on the `output_trialN.txt` files it was made from. What does not reproduce, and why:

- one shading, s12 under `-e relevant`: the paper shades it 10-100x, which is the factor over
  the plain time rounded to 0.001 (93x); over the unrounded medians it is 147x. The test
  accepts the paper's cell as a rounding of the plain time.
- the largest slowdown the prose cites, 908.7x: it is s11 unrestricted over its plain time
  rounded to 0.061, as the table prints it; over the unrounded median it is 911.3x.
- the tests: every p-value and effect size of the two tests tables of the submitted paper
  (`test_submitted_tests`) comes out of the procedure of the notebook that produced them
  ("Analise Estatistica.ipynb", 2026, found after this generator was written), and only of
  it: the values as the tables print them (times rounded to 0.001 s, sizes to the MiB);
  `scipy.stats.wilcoxon(differences, alternative="greater")`, a one-sided test with scipy's
  defaults (zero differences dropped); Bonferroni within each set of comparisons, three for
  granularity and two against plain Python, not over the five of the table; the
  rank-biserial correlation over the non-zero differences. The paper's text says none of the
  three choices that matter (one-sided, rounded values, two families). The notebook's saved
  outputs hold the storage numbers in the place of the time granularity numbers, because its
  second cell redefines the lists of the first; the time rows were run before that cell.
  The same procedure on the unrounded medians gives the same verdicts and slightly different
  p-values (`test_time_tests`, `test_space_tests`).
"""

import pathlib
import re

import pytest

import paper_tables as pt

HERE = pathlib.Path(__file__).resolve().parent
LEGACY = HERE.parent / "experimental_analysis" / "results"

TIMES = r"""
        $s1$    &   1.041   &   \ovhA 5.367&   \ovhA 5.304& \ovhA 2.860&   \ovhA 3.196 & \ovhA 3.207    & \ovhA 2.538    &   \ovhA 2.405 &    1.515\\
        $s2$    &   1.208   &   \ovhC 793.752&   \ovhC 794.608& \ovhA 3.920&   \ovhC 787.401& \ovhC 790.369      & \ovhA 3.640    &   \ovhA 10.277 &   \ovhA 9.719\\
        $s3$    &   0.422   &   \ovhA 1.003&   \ovhA 0.988&  0.837&   \ovhA 0.851& \ovhA 0.877    &  0.817    &    0.786 &    0.714\\
        $s4$    &   0.010   &   \ovhB 0.146&   \ovhB 0.142& \ovhA 0.040&   \ovhA 0.071& \ovhA 0.067    & \ovhA 0.040    &   \ovhB 0.101 &   \ovhA 0.091\\
        $s5$    &   0.011   &   \ovhB 0.502&   \ovhB 0.498& \ovhA 0.079&   \ovhB 0.234& \ovhB 0.236    & \ovhA 0.080    &   \ovhB 0.346 &   \ovhB 0.331\\
        $s6$    &   0.001$^\dagger$   &   \ovhC 0.300&   \ovhC 0.309& \ovhC 0.162&   \ovhC 0.207& \ovhC 0.204    & \ovhC 0.135    &   \ovhC 0.227 &   \ovhC 0.207\\
        $s7$    &   0.026   &   \ovhB 2.446&   \ovhB 0.921& \ovhB 0.847&   \ovhB 2.081& \ovhB 0.562    & \ovhB 0.511    &   \ovhB 0.785 &   \ovhB 0.639\\
        $s8$    &   $ < 0.001$$^\dagger$  &   \ovhC 0.007&   \ovhB 0.004& \ovhB 0.002&   \ovhB 0.003& \ovhB 0.002    & \ovhB 0.002    &   \ovhC 0.007 &   \ovhC 0.006\\
        $s9$    &   0.004$^\dagger$   &   \ovhB 0.091&   \ovhB 0.087& \ovhB 0.087&   \ovhB 0.067& \ovhB 0.062    & \ovhB 0.062    &   \ovhB 0.085 &   \ovhB 0.077\\
        $s10$   &   0.001$^\dagger$   &   \ovhC 0.144&   \ovhC 0.144& \ovhC 0.146&   \ovhC 0.118& \ovhC 0.119    & \ovhC 0.118    &   \ovhC 0.137 &   \ovhC 0.131\\
        $s11$   &   0.061   &   \ovhC 55.428&   \ovhC 53.295& \ovhB 2.473&   \ovhC 55.406& \ovhC 55.355   & \ovhB 2.526    &   \ovhC 49.871 &   \ovhC 50.361\\
        $s12$   &   0.001$^\dagger$   &   \ovhC 0.154&   \ovhC 0.148& \ovhB 0.012&   \ovhC 0.153& \ovhC 0.156    & \ovhB 0.044    &   \ovhB 0.093 &   \ovhB 0.063\\
        $s13$   &   827.217 &    932.940&    925.799&  839.609&    882.921&  889.742    &  840.259    &    882.412 &    831.846\\
        $s14$   &   485.993 &   -       & -     &   -   &   -   &   -   &   -   &   - &   -     \\
        $s15$   &   132.482 & 232.650   & 232.045   & 154.897   & 217.651   &  217.910      &  153.850    & 201.311 & 153.939   \\
        $s16$   &   34.641  & 34.903    & 34.909    & 34.555    & 34.579    &  34.545       &  34.599     & 34.933  & 34.904    \\
        $s17$   &   44.211  & 43.834    & 43.689    & 43.711    & 44.122    &  44.087       &  43.933     & 43.563  & 43.773    \\
        $s18$   &   53.317  & 53.305    & 53.359    & 53.359    & 53.413    &  53.338       &  53.285     & 53.294  & 53.286    \\
        $s19$   &   84.628  & 131.863   & 132.159   & 93.684    & 124.917   &  124.995      &  93.035     & 118.954 & 104.541   \\
        $s20$   &   270.138 &   -       & -     &   -   &   -   &   -   &   -   &   - &   -     \\
        $s21$   &   59.354 &   -        & -     &   -   &   -   &   -   &   -   &   - &   -     \\
"""

SPACE = r"""
        $s1$   &   14   &    163     & 163      &    96  & 108    &    108     &    90  & 102 & 78  \\
        $s2$   &   144  &    22,725  & 22,725   &    87  & 22,689 &    22,689  &    84  & 355 & 344 \\
        $s3$   &   $<$1    &    71  & 71  &    66  & 67  &    67  &    66  & 67 & 65  \\
        $s4$   &   18   &    25  & 25  &    21  & 23  &    23  &    21  & 25 & 25  \\
        $s5$   &   155  &    35  & 35  &    21  & 26  &    26  &    21  & 32 & 32  \\
        $s6$   &   0        &    28  & 28  &    19  & 23  &    23  &    18  & 23 & 22  \\
        $s7$   &   0        &    75  & 53  &    52  & 72  &    51  &    50  & 73 & 73  \\
        $s8$   &   0        &    2   & 1   &    1   & 1   &    1   &    1   & 2 & 2   \\
        $s9$   &   0        &    6   & 6   &    6   & 4   &    4   &    4   & 6 & 6   \\
        $s10$  &   0        &    20  & 20  &    20  & 19  &    19  &    19  & 20 & 20  \\
        $s11$  &   $<$1    &    1,896    & 1,896    &    5   & 1,893    &    1,893   &     5   & 1,881 & 1,877    \\
        $s12$  &   $<$1    &    37  & 37  &    33  & 34  &  34  &    33    & 37 & 37  \\
        $s13$  &   0        &    790 & 790 &    27  & 238 &    238 &    27  & 723 & 643 \\
        $s14$  &   0        &   -   &   -   &   -   &   -   &   -   &   -   &   - &     -   \\
        $s15$  &   0        &    459 & 459 &    43  & 411 &    411 &    43  & 439 &    413 \\
        $s16$  &   0        &    15  & 15  &    15  & 15  &    15  &    15  & 15 &    15  \\
        $s17$  &   0        &    64  & 64  &    64  & 32  &    32  &    32  & 62 & 62  \\
        $s18$  &   0        &    15  & 15  &    15  & 15  &    15  &    15  & 15 & 15  \\
        $s19$  &   0        &    258 & 258 &    29  & 230 &    230 &    29  & 246 & 235 \\
        $s20$  &   0        &   -   &   -   &   -   &   -   &   -   &   -   &   - &     -   \\
        $s21$  &   0        &   -   &   -   &   -   &   -   &   -   &   -   &   - &     -   \\
"""

# Tables 6 and 8 of the submitted paper: Shapiro-Wilk p, Wilcoxon p (Bonferroni), effect size.
TIME_TESTS = [("<0.001", 0.004, 0.778, "large"), ("<0.001", 0.016, 0.684, "large"),
              ("0.012", 0.416, 0.309, "medium"), ("<0.001", 0.001, 0.871, "large"), ("<0.001", 0.002, 0.801, "large")]
SPACE_TESTS = [("<0.001", 0.001, 1.000, "large"), ("<0.001", 0.001, 1.000, "large"), ("<0.001", 0.026, 1.000, "large")]


def rows(body):
    """The data rows of a table body, each as its cells with spaces and dollars removed."""
    out = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("$s"):
            continue
        cells = [re.sub(r"[\s$]", "", c) for c in line.rstrip("\\").split("&")]
        out.append(cells)
    return out


@pytest.fixture(scope="module")
def legacy(tmp_path_factory):
    ds = pt.load_legacy(LEGACY)
    out = tmp_path_factory.mktemp("tables")
    summary = pt.generate(ds, out, correction="bonferroni", method="approx", scale="linear")
    return ds, out, summary


def test_ten_repetitions(legacy):
    ds, _, _ = legacy
    assert ds.repetitions == list(range(1, 11))
    assert ds.finished(*pt.COLUMNS) == [s for s in pt.SIDS if s not in ("s14", "s20", "s21")]


def test_times_table(legacy):
    _, out, _ = legacy
    got, expected = rows((out / "overhead-times.tex").read_text()), rows(TIMES)
    assert len(got) == len(expected)
    for g, e in zip(got, expected):
        if g[0] == "s12":
            assert g[8] == r"\ovhC0.093" and e[8] == r"\ovhB0.093"  # the documented rounding of the paper
            g, e = g[:8] + g[9:], e[:8] + e[9:]
        assert g == e


def test_space_table(legacy):
    _, out, _ = legacy
    assert rows((out / "overhead-space.tex").read_text()) == rows(SPACE)


def test_average_ranks(legacy):
    _, _, s = legacy
    time_ranks, space_ranks = s["average_rank_time"], s["average_rank_space"]
    # The paper: the largest overheads in fg and fg -d3, the smallest in cg -d2 and fg -d2 (time),
    # and in both depth-2 configurations (space).
    assert sorted(time_ranks, key=time_ranks.get)[-2:] == ["d3", "now"] or sorted(time_ranks, key=time_ranks.get)[-2:] == ["now", "d3"]
    assert set(sorted(time_ranks, key=time_ranks.get)[:2]) == {"cg-d2", "d2"}
    assert set(sorted(space_ranks, key=space_ranks.get)[-2:]) == {"now", "d3"}
    assert set(sorted(space_ranks, key=space_ranks.get)[:2]) == {"cg-d2", "d2"}


def test_prose_numbers(legacy):
    _, _, s = legacy
    assert (round(s["max_slowdown"][0], 1), s["max_slowdown"][1]) == (911.3, "s11")  # the paper: 908.7, see the docstring
    assert round(s["max_slowdown_long_scripts_finished"][0], 1) == 1.8
    assert round(s["max_overhead_s_long_scripts_finished"][0], 1) == 105.7
    assert (s["short_scripts_runs"], s["short_scripts_runs_under_1s"]) == (96, 71)
    assert (s["short_scripts_runs_without_s1_s2_s11"], s["short_scripts_runs_under_1s_without_s1_s2_s11"]) == (72, 70)
    assert round(100 * s["median_time_reduction_fg_to_cg"], 1) == 10.7
    top = list(s["store_reduction_fg_minus_cg_mib"].items())[:3]
    assert [sid for sid, _ in top] == ["s13", "s1", "s15"]
    assert [round(mib) for _, mib in top] == [552, 55, 47]  # the paper: 48 for s15, from the rounded sizes (459 - 411)


def test_time_tests(legacy):
    _, _, s = legacy
    for row, (shapiro, _, r, label) in zip(s["time_tests"], TIME_TESTS):
        assert pt.fmt_p(row["shapiro"]).replace("$", "").replace(" ", "") == shapiro
        assert row["r"] == pytest.approx(r, abs=0.0015)
        assert row["label"] == label
    assert [row["family_size"] for row in s["time_tests"]] == [3, 3, 3, 2, 2]
    assert [round(row["wilcoxon_raw"], 3) for row in s["time_tests"]] == [0.004, 0.011, 0.248, 0.001, 0.003]
    assert [row["wilcoxon"] < 0.05 for row in s["time_tests"]] == [p < 0.05 for _, p, _, _ in TIME_TESTS]


def _submitted(ds, families, value):
    """The notebook's procedure: rounded values, one-sided scipy defaults, Bonferroni per family;
    the p-values as the tables print them, the effect sizes and their labels."""
    sids = ds.finished(*pt.COLUMNS)
    rows = []
    for family in families:
        fam = [pt.paired_test([value(ds.cell(s, a)) for s in sids], [value(ds.cell(s, b)) for s in sids],
                              method="scipy", scale="linear", alternative="greater") for _, a, b in family]
        for t, p in zip(fam, pt.adjust([t["wilcoxon_raw"] for t in fam], "bonferroni")):
            rows.append((pt.fmt_p(p).replace("$", "").replace(" ", ""), round(t["r"], 3), t["label"]))
    return rows


def test_submitted_tests(legacy):
    ds, _, _ = legacy
    time = _submitted(ds, pt.TIME_FAMILIES, lambda c: round(c.time, 3))
    space = _submitted(ds, pt.SPACE_FAMILIES, lambda c: round(c.store_mib))
    # Tables 6 and 8 of the submitted paper, as printed.
    assert time == [("0.004", 0.778, "large"), ("0.016", 0.684, "large"), ("0.416", 0.309, "medium"),
                    ("<0.001", 0.871, "large"), ("0.002", 0.801, "large")]
    assert space == [("0.001", 1.0, "large"), ("0.001", 1.0, "large"), ("0.026", 1.0, "large")]


def test_space_tests(legacy):
    _, _, s = legacy
    for row, (shapiro, p, r, label) in zip(s["space_tests"], SPACE_TESTS):
        assert pt.fmt_p(row["shapiro"]).replace("$", "").replace(" ", "") == shapiro
        if row["left"] != "d2":
            assert round(row["wilcoxon"], 3) == p
            assert round(row["r"], 3) == r
        assert row["label"] == label
    assert round(s["space_tests"][2]["wilcoxon"], 3) == 0.001
    assert round(s["space_tests"][2]["r"], 3) == 0.942  # the paper: 1.000 on the rounded sizes



def test_holm_never_rejects_less_than_bonferroni():
    p = [0.001, 0.02, 0.03, 0.2, 0.6]
    holm, bonf = pt.adjust(p, "holm"), pt.adjust(p, "bonferroni")
    assert all(h <= b for h, b in zip(holm, bonf))
    assert holm == [0.005, 0.08, 0.09, 0.4, 0.6]
    assert holm == sorted(holm)
