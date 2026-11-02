"""The tables of the paper's Section 7.3, from a results directory of the gate.

usage: python3 paper_tables.py RESULTS --out DIR [--min-repetitions N] [--correction holm|bonferroni]

Needs numpy and scipy (`uv run --with scipy python3 paper_tables.py ...`).

RESULTS is a directory gate.py wrote (`correctness/<sid>/<config>.json` and
`timing/<sid>/<config>/rep<NN>.json`). DIR receives LaTeX fragments, each the
body of one table of the paper, which `main.tex` includes with `\\input`:

  overhead-times.tex        tab:experimentsTableTimes          times, shading, markers
  overhead-times-tests.tex  tab:statisticalTestTimeOverhead1   five paired comparisons, with n
  overhead-space.tex        tab:experimentsTableProvenanceStored  store sizes in MiB
  overhead-space-tests.tex  tab:statisticalTestSpaceOverhead   three paired comparisons
  overhead-process-times.tex tab:experimentsTableProcessTimes  wall-clock time of the whole
                                                               process

and `overhead-summary.json`, the numbers the prose of the section cites (ranks, extremes,
counts, the runs that did not finish), so that the text can be checked against the data.

What the tables hold, and how it is computed:

- The time of a run is the one the script prints on its last line (`reported`), measured by
  the script around its own body with `perf_counter`: it excludes the start of the interpreter
  and of noWorkflow and the writing of the store. The gate also records the wall-clock time of
  the whole process (`wall`), which includes them; `overhead-process-times.tex` is the same
  table for that time, and the summary holds its tests and its difference to the reported time
. A script
  and configuration pair gets the median over the complete repetitions: a repetition counts only when it holds every pair the pass timed
  (the pairs that did not finish in the correctness pass are not timed). The table prints
  three decimals, `$<$ 0.001` below 0.0005, and marks with a dagger the plain Python times
  that print below 0.010, whose slowdown factors are inflated by the short baseline.
- The slowdown factor of a cell is its time over the plain Python time of the same script,
  both unrounded; the shading is `\\ovhA` from 2x, `\\ovhB` from 10x and `\\ovhC` from 100x.
- A pair that did not finish is marked instead of a number: `$\\ddagger$` for a run the memory
  cap ended (status `oom`).
- The store of a pair is the size of `.noworkflow/` in bytes (`store_bytes` of the run of
  the correctness pass), which does not depend on
  the repetition (a run of the timing pass that differs by more than 0.1% is reported); the
  table prints it in MiB rounded to the nearest integer, `$<$1` when it rounds to zero, and
  the tests use the unrounded sizes. The accessed data size column is a property of the
  scripts (`DATA_MIB`), not of a run.
- The average rank of a configuration (overall analysis of the paper) ranks the eight
  configurations of each script from 1 (lowest time, or store) to 8, ties averaged, over
  the scripts that finished under all eight, and averages the ranks per configuration.
- The paired comparisons follow the paper's methodology: n = the scripts that finished under
  both configurations; Shapiro-Wilk on the paired differences; Wilcoxon signed-rank test,
  two-sided by default (`--alternative greater` tests that the first configuration of each
  pair is the slower, or the larger), on the exact distribution
  of the statistic (`--method approx` is the normal approximation without continuity
  correction and with the zero differences kept in the ranking; `--method scipy` is
  `scipy.stats.wilcoxon` with its defaults, zero differences dropped); on the differences of the logarithms, that is, on the ratio between
  the two configurations: a halving and a doubling are then the same distance from no change,
  and the test is about the slowdown factors the tables show rather than about seconds, where
  the longest scripts would dominate (`--scale linear` tests the differences as they are).
  The p-values are
  adjusted within each set of comparisons the paper describes: the three that contrast fine-
  and coarse-grained collection, and the two against plain Python (time only), with Holm's
  step-down procedure, which controls the family-wise error rate as Bonferroni does and
  rejects at least as much (`--correction bonferroni` is the classical alternative). The
  effect size is the rank-biserial correlation
  r = (W+ - W-) / (W+ + W-) over the non-zero differences, labelled small below 0.3, medium
  below 0.5 and large from 0.5. The Wilcoxon test is used because the differences are not
  normal (the Shapiro-Wilk column shows it) and the sample is small; it is a test of the
  consistency of the sign of the differences across scripts, not of their magnitude, which is
  why the paper reports the effect size next to it.
"""

import argparse
import datetime
import json
import math
import pathlib
import re
import statistics
import sys

import numpy as np
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare import UNFINISHED  # noqa: E402
from scripts import CONFIGS, SCRIPTS  # noqa: E402

SIDS = [sid for sid, _, _ in SCRIPTS]
# Columns of the tables, after plain Python, in the paper's order.
COLUMNS = ["now", "d3", "d2", "cg", "cg-d3", "cg-d2", "e-relevant", "e-none"]
# The comparisons of the two tests tables: label, left, right.
TIME_PAIRS = [
    ("fine-grained versus coarse-grained", "now", "cg"),
    ("fine-grained-depth-3 versus coarse-grained-depth-3", "d3", "cg-d3"),
    ("fine-grained-depth-2 versus coarse-grained-depth-2", "d2", "cg-d2"),
    ("fine-grained versus baseline", "now", "python"),
    ("coarse-grained-depth-2 versus baseline", "cg-d2", "python"),
]
SPACE_PAIRS = TIME_PAIRS[:3]
# The sets of comparisons whose p-values are adjusted together (the paper's two sets of pairwise
# comparisons: granularity, and the range against plain Python).
TIME_FAMILIES = [TIME_PAIRS[:3], TIME_PAIRS[3:]]
SPACE_FAMILIES = [SPACE_PAIRS]
# Size of the data each script reads, in MiB (Table 1 of the paper, "Accessed Data Size").
DATA_MIB = {"s1": "14", "s2": "144", "s3": "$<$1", "s4": "18", "s5": "155", "s11": "$<$1", "s12": "$<$1"}
UNFINISHED_MARK = {"timeout": "-", "oom": r"$\ddagger$"}
SHADE = [(100, r"\ovhC"), (10, r"\ovhB"), (2, r"\ovhA")]
MIB = 2**20
TIME = re.compile(r"^-?\d+[.,]\d+(e-?\d+)?$")


class Cell:
    """One script and configuration pair: its times, its store, or why it did not finish."""

    def __init__(self, times=(), store_bytes=None, unfinished=None, wall=None, peak_rss=None, walls=()):
        self.times = list(times)
        self.walls = list(walls)  # wall-clock of the whole process, same repetitions as times
        self.store_bytes = store_bytes
        self.unfinished = unfinished  # None, "timeout" or "oom"
        self.wall = wall  # of the unfinished run
        self.peak_rss = peak_rss

    @property
    def time(self):
        return statistics.median(self.times) if self.times else None

    @property
    def process_time(self):
        return statistics.median(self.walls) if self.walls else None

    @property
    def store_mib(self):
        return None if self.store_bytes is None else self.store_bytes / MIB


class Dataset:
    def __init__(self, source, cells, repetitions, note=""):
        self.source = source
        self.cells = cells  # sid -> config -> Cell
        self.repetitions = repetitions  # the complete repetitions the medians are over
        self.note = note

    def cell(self, sid, cfg):
        return self.cells[sid][cfg]

    def finished(self, *cfgs):
        return [sid for sid in SIDS if all(self.cell(sid, c).unfinished is None for c in cfgs)]


# ----------------------------------------------------------------------------- loading

def load_gate(root, min_repetitions=1):
    """A results directory of gate.py: the timing pass for the times, the correctness pass
    for the stores and for the runs that did not finish."""
    root = pathlib.Path(root)
    cells = {sid: {} for sid in SIDS}
    for sid in SIDS:
        for cfg in ["python"] + COLUMNS:
            p = root / "correctness" / sid / f"{cfg}.json"
            r = json.loads(p.read_text())
            if r["status"] in UNFINISHED:
                cells[sid][cfg] = Cell(unfinished="oom", wall=r["wall"], peak_rss=r["peak_rss"],
                                       store_bytes=r["store_bytes"])
            else:
                cells[sid][cfg] = Cell(store_bytes=r["store_bytes"] if cfg != "python" else None)
    timed = [(sid, cfg) for sid in SIDS for cfg in ["python"] + COLUMNS if cells[sid][cfg].unfinished is None]
    by_rep = {}  # repetition -> {(sid, cfg): record}
    for sid, cfg in timed:
        d = root / "timing" / sid / cfg
        for p in sorted(d.glob("rep*.json")) if d.is_dir() else []:
            r = json.loads(p.read_text())
            if r["status"] in UNFINISHED:
                continue
            if r["reported"] is None:
                raise SystemExit(f"{p}: no reported time")
            by_rep.setdefault(r["repetition"], {})[(sid, cfg)] = r
    complete = sorted(n for n, recs in by_rep.items() if len(recs) == len(timed))
    if len(complete) < min_repetitions:
        raise SystemExit(f"{len(complete)} complete repetitions ({len(timed)} pairs each), {min_repetitions} required")
    for sid, cfg in timed:
        cell = cells[sid][cfg]
        cell.times = [by_rep[n][(sid, cfg)]["reported"] for n in complete]
        cell.walls = [by_rep[n][(sid, cfg)]["wall"] for n in complete]
        if cfg != "python":
            stores = {by_rep[n][(sid, cfg)]["store_bytes"] for n in complete}
            if any(abs(b - cell.store_bytes) > 0.001 * cell.store_bytes for b in stores):
                print(f"warning: {sid} {cfg}: store of the correctness pass {cell.store_bytes}, of the timing pass {sorted(stores)}",
                      file=sys.stderr)
    cand = json.loads((root / "candidate.json").read_text())
    note = f"{cand['version']} ({cand['sha256'][:12]}), Python {cand['python']}"
    return Dataset(str(root), cells, complete, note)


def fmt_time(t):
    return r"$<$ 0.001" if t < 0.0005 else f"{t:.3f}"


def fmt_mib(mib):
    n = int(math.floor(mib + 0.5))
    return r"$<$1" if n == 0 else f"{n:,}"


def shade(factor):
    for threshold, macro in SHADE:
        if factor >= threshold:
            return macro + " "
    return ""


def effect_label(r):
    r = abs(r)
    return "small" if r < 0.3 else "medium" if r < 0.5 else "large"


def fmt_p(p):
    return r"$<$ 0.001" if p < 0.0005 else f"{p:.3f}"


def paired_test(x, y, method="exact", scale="log", alternative="two-sided"):
    """Shapiro-Wilk p on the differences, the raw Wilcoxon p, the rank-biserial r.

    method: "exact" enumerates the 2^n sign assignments of the ranks (no ties, no zeros);
    "approx" is the normal approximation without continuity correction, zeros kept (Pratt);
    "scipy" is scipy.stats.wilcoxon with its defaults (zeros dropped, the exact distribution
    or the normal approximation as scipy chooses). alternative: "two-sided", or "greater"
    (x > y, one-sided). scale: "log" tests the differences of the logarithms,
    that is, the ratio between the two configurations, on the scale where a halving and a
    doubling are the same distance from no change; "linear" tests the differences as they are.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if scale == "log":
        x, y = np.log(x), np.log(y)
    d = x - y
    shapiro = float(stats.shapiro(d).pvalue)
    if method == "exact":
        wilcoxon = float(stats.wilcoxon(x, y, zero_method="wilcox", method="exact", alternative=alternative).pvalue)
    elif method == "scipy":
        wilcoxon = float(stats.wilcoxon(d, alternative=alternative).pvalue)
    else:
        wilcoxon = float(stats.wilcoxon(x, y, zero_method="pratt", correction=False, method="approx",
                                        alternative=alternative).pvalue)
    nz = d[d != 0]
    ranks = stats.rankdata(np.abs(nz))
    plus, minus = ranks[nz > 0].sum(), ranks[nz < 0].sum()
    r = float((plus - minus) / (plus + minus)) if plus + minus else 0.0
    return {"n": len(d), "shapiro": shapiro, "wilcoxon_raw": wilcoxon, "r": r, "label": effect_label(r)}


def adjust(pvalues, method):
    """The p-values of one family, adjusted: Holm's step-down (each sorted p times the number
    of hypotheses not yet rejected, made monotone) or Bonferroni (each times the family size)."""
    m = len(pvalues)
    if method == "bonferroni":
        return [min(1.0, p * m) for p in pvalues]
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, pvalues[i] * (m - rank))
        adjusted[i] = min(1.0, running)
    return adjusted


def average_ranks(ds, value):
    """Per configuration, the average over the scripts that finished under all eight of the
    rank of its value among the eight (1 = lowest, ties averaged)."""
    sids = ds.finished(*COLUMNS)
    total = {c: 0.0 for c in COLUMNS}
    for sid in sids:
        ranks = stats.rankdata([value(ds.cell(sid, c)) for c in COLUMNS])
        for c, rk in zip(COLUMNS, ranks):
            total[c] += rk
    return {c: total[c] / len(sids) for c in COLUMNS}, sids


# ----------------------------------------------------------------------------- tables

def header(first):
    return (
        r"    \begin{tabular}{@{} l r r r r r r r r r r}" "\n"
        r"      \toprule" "\n"
        r"      \multicolumn{1}{c}{ID} & \multicolumn{1}{c}{" + first[0] + r"}  &  \multicolumn{1}{c}{fg}  & \multicolumn{1}{c}{fg} & \multicolumn{1}{c}{fg} & \multicolumn{1}{c}{cg} & \multicolumn{1}{c}{cg} & \multicolumn{1}{c}{cg} & \multicolumn{1}{c}{fv} & \multicolumn{1}{c}{nv}   \\" "\n"
        r"      \multicolumn{1}{c}{}   & \multicolumn{1}{c}{" + first[1] + r"} &  \multicolumn{1}{c}{}            & \multicolumn{1}{c}{(-d3)}      & \multicolumn{1}{c}{(-d2)}     & \multicolumn{1}{c}{(-cg)}        & \multicolumn{1}{c}{(-cg -d3)}    & \multicolumn{1}{c}{(-cg -d2)}    & \multicolumn{1}{c}{(-e relevant)} & \multicolumn{1}{c}{(-e none)} \\" "\n"
        r"      \midrule" "\n"
    )


FOOTER = "      \\bottomrule\n    \\end{tabular}\n"


def times_table(ds, value=lambda c: c.time):
    out = header(("Plain", "Python"))
    for sid in SIDS:
        plain = value(ds.cell(sid, "python"))
        cells = [fmt_time(plain) + (r"$^\dagger$" if round(plain, 3) < 0.01 else "")]
        for cfg in COLUMNS:
            c = ds.cell(sid, cfg)
            if c.unfinished:
                cells.append(UNFINISHED_MARK[c.unfinished])
            else:
                cells.append(shade(value(c) / plain) + fmt_time(value(c)))
        out += f"        ${sid}$ & " + " & ".join(cells) + " \\\\\n"
    out += FOOTER
    out += (
        "    \\begin{tabular}{lcccc}\n"
        "    Slowdown: & $<2\\times$ & \\ovhA $2$--$10\\times$ & \\ovhB $10$--$100\\times$ & \\ovhC $\\geq 100\\times$ \\\\\n"
        "    \\end{tabular}\n"
    )
    return out


def space_table(ds):
    out = header(("Accessed", "Data Size"))
    for sid in SIDS:
        cells = [DATA_MIB.get(sid, "0")]
        for cfg in COLUMNS:
            c = ds.cell(sid, cfg)
            cells.append(UNFINISHED_MARK[c.unfinished] if c.unfinished else fmt_mib(c.store_mib))
        out += f"        ${sid}$ & " + " & ".join(cells) + " \\\\\n"
    return out + FOOTER


def tests(ds, families, value, correction, method="exact", scale="log", alternative="two-sided"):
    """The rows of one tests table: families is a list of lists of pairs, and the p-values are
    adjusted within each family (the paper's sets of comparisons)."""
    rows = []
    for family in families:
        fam = []
        for label, a, b in family:
            sids = ds.finished(a, b)
            t = paired_test([value(ds.cell(s, a)) for s in sids], [value(ds.cell(s, b)) for s in sids],
                            method, scale, alternative)
            fam.append({"comparison": label, "left": a, "right": b, "scripts": sids, "family_size": len(family), **t})
        for row, p in zip(fam, adjust([r["wilcoxon_raw"] for r in fam], correction)):
            row["wilcoxon"] = p
            row.update(correction=correction, method=method, scale=scale, alternative=alternative)
        rows += fam
    return rows


def tests_table(rows, baseline_rule=True):
    out = (
        r"    \begin{tabular}{@{} c c c c c @{}}" "\n"
        r"      \toprule" "\n"
        r"        Comparison  & $n$ & Shapiro-Wilk test  &  Wilcoxon test  & Effect Size \\" "\n"
        r"      \midrule" "\n"
    )
    for i, row in enumerate(rows):
        if baseline_rule and i == 3:
            out += "      \\midrule\n"
        out += f"        {row['comparison']} & {row['n']} & {fmt_p(row['shapiro'])} & {fmt_p(row['wilcoxon'])} & {row['r']:.3f} ({row['label']}) \\\\\n"
    return out + FOOTER


# ----------------------------------------------------------------------------- summary

def summary(ds, time_tests, space_tests, process_tests=None):
    time_ranks, ranked = average_ranks(ds, lambda c: c.time)
    space_ranks, _ = average_ranks(ds, lambda c: c.store_mib)
    short = [sid for sid in SIDS[:12]]
    cells = {sid: {cfg: ds.cell(sid, cfg) for cfg in ["python"] + COLUMNS} for sid in SIDS}
    factors = {sid: {cfg: cells[sid][cfg].time / cells[sid]["python"].time for cfg in COLUMNS if cells[sid][cfg].time is not None}
               for sid in SIDS}
    overhead_s = {sid: {cfg: cells[sid][cfg].time - cells[sid]["python"].time for cfg in COLUMNS if cells[sid][cfg].time is not None}
                  for sid in SIDS}
    under_1s = [(sid, cfg) for sid in short for cfg, o in overhead_s[sid].items() if o < 1]
    heavy = {"s1", "s2", "s11"}
    under_1s_rest = [(s, c) for s, c in under_1s if s not in heavy]
    runs_rest = sum(len(overhead_s[s]) for s in short if s not in heavy)
    fg_cg = {sid: 1 - cells[sid]["cg"].time / cells[sid]["now"].time for sid in ds.finished("now", "cg")}
    store_reduction = {sid: (cells[sid]["now"].store_mib - cells[sid]["cg"].store_mib) for sid in ds.finished("now", "cg")}
    unfinished = [{"sid": sid, "config": cfg, "wall_s": c.wall, "peak_gib": c.peak_rss / 2**30 if c.peak_rss else None,
                   "store_mib": c.store_mib}
                  for sid in SIDS for cfg in COLUMNS for c in [cells[sid][cfg]] if c.unfinished]
    has_wall = all(cells[sid][cfg].process_time is not None for sid in SIDS for cfg in ["python"] + COLUMNS
                   if cells[sid][cfg].unfinished is None)
    process = {}
    if has_wall:
        extra = {sid: {cfg: cells[sid][cfg].process_time - cells[sid][cfg].time for cfg in ["python"] + COLUMNS
                       if cells[sid][cfg].process_time is not None} for sid in SIDS}
        by_cfg = {cfg: sorted((extra[sid][cfg], sid) for sid in SIDS if cfg in extra[sid]) for cfg in ["python"] + COLUMNS}
        process = {
            "process_time_s": {sid: {cfg: cells[sid][cfg].process_time for cfg in ["python"] + COLUMNS
                                     if cells[sid][cfg].process_time is not None} for sid in SIDS},
            "process_slowdown": {sid: {cfg: cells[sid][cfg].process_time / cells[sid]["python"].process_time
                                       for cfg in COLUMNS if cells[sid][cfg].process_time is not None} for sid in SIDS},
            # what the whole process adds to the script's own time: start-up and the writing of the store
            "process_minus_reported_s": extra,
            "process_minus_reported_by_config": {cfg: {"median": statistics.median(v for v, _ in xs), "min": xs[0], "max": xs[-1]}
                                                 for cfg, xs in by_cfg.items()},
            "median_process_slowdown": {cfg: statistics.median(cells[sid][cfg].process_time / cells[sid]["python"].process_time
                                                              for sid in ds.finished(cfg)) for cfg in COLUMNS},
        }
    return {
        "source": ds.source, "note": ds.note, "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "repetitions": ds.repetitions,
        "scripts_finished_under_all": ranked,
        "average_rank_time": time_ranks, "average_rank_space": space_ranks,
        "slowdown": factors, "overhead_s": overhead_s,
        "max_slowdown": max((f, s, c) for s in SIDS for c, f in factors[s].items()),
        "max_slowdown_long_scripts_finished": max((f, s, c) for s in SIDS[12:] for c, f in factors[s].items()) if any(factors[s] for s in SIDS[12:]) else None,
        "max_overhead_s_long_scripts_finished": max((o, s, c) for s in SIDS[12:] for c, o in overhead_s[s].items()) if any(overhead_s[s] for s in SIDS[12:]) else None,
        "short_scripts_runs": sum(len(overhead_s[s]) for s in short),
        "short_scripts_runs_under_1s": len(under_1s),
        "short_scripts_runs_without_s1_s2_s11": runs_rest,
        "short_scripts_runs_under_1s_without_s1_s2_s11": len(under_1s_rest),
        "median_time_reduction_fg_to_cg": statistics.median(fg_cg.values()),
        "store_mib": {sid: {cfg: cells[sid][cfg].store_mib for cfg in COLUMNS} for sid in SIDS},
        "store_reduction_fg_minus_cg_mib": dict(sorted(store_reduction.items(), key=lambda kv: -kv[1])),
        "unfinished": unfinished, "process_time_tests": process_tests,
        "time_tests": time_tests, "space_tests": space_tests,
        **process,
    }


# ----------------------------------------------------------------------------- main

def generate(ds, out, correction="holm", method="exact", scale="log", alternative="two-sided"):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = (f"% Generated by release-gate/paper_tables.py of noworkflow-overhead-experiments from {ds.source}\n"
             f"% ({ds.note}; median over {len(ds.repetitions)} complete repetitions; Wilcoxon {method}, {alternative}, on the {scale} scale, p-values adjusted by {correction} within each set of comparisons). Do not edit: regenerate.\n")
    time_tests = tests(ds, TIME_FAMILIES, lambda c: c.time, correction, method, scale, alternative)
    space_tests = tests(ds, SPACE_FAMILIES, lambda c: c.store_mib, correction, method, scale, alternative)
    fragments = {
        "overhead-times.tex": times_table(ds),
        "overhead-times-tests.tex": tests_table(time_tests),
        "overhead-space.tex": space_table(ds),
        "overhead-space-tests.tex": tests_table(space_tests, baseline_rule=False),
    }
    process_tests = None
    if all(ds.cell(sid, cfg).process_time is not None for sid in SIDS for cfg in ["python"] + COLUMNS
           if ds.cell(sid, cfg).unfinished is None):
        fragments["overhead-process-times.tex"] = times_table(ds, lambda c: c.process_time)
        process_tests = tests(ds, TIME_FAMILIES, lambda c: c.process_time, correction, method, scale, alternative)
    for name, body in fragments.items():
        (out / name).write_text(stamp + body)
    s = summary(ds, time_tests, space_tests, process_tests)
    (out / "overhead-summary.json").write_text(json.dumps(s, indent=1, default=str) + "\n")
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("results", help="a results directory of gate.py")
    ap.add_argument("--out", required=True, help="where the fragments go (the paper's tables/ directory)")
    ap.add_argument("--min-repetitions", type=int, default=1, help="refuse fewer complete repetitions (gate results)")
    ap.add_argument("--correction", choices=["holm", "bonferroni"], default="holm", help="adjustment of the p-values of each table")
    ap.add_argument("--method", choices=["exact", "approx", "scipy"], default="exact", help="the Wilcoxon p-value: the exact distribution, the normal approximation, or scipy's defaults")
    ap.add_argument("--alternative", choices=["two-sided", "greater"], default="two-sided", help="two-sided, or one-sided: the first configuration of each pair is the slower or larger")
    ap.add_argument("--scale", choices=["linear", "log"], default="log", help="test the differences of the logarithms (the ratio between configurations), or the differences as they are")
    args = ap.parse_args()
    ds = load_gate(args.results, args.min_repetitions)
    s = generate(ds, args.out, args.correction, args.method, args.scale, args.alternative)
    print(f"{ds.note}: median over repetitions {ds.repetitions}; {len(s['scripts_finished_under_all'])} scripts finished under all configurations")
    for u in s["unfinished"]:
        print(f"  did not finish: {u['sid']} {u['config']}" + (f" after {u['wall_s']:.0f} s at {u['peak_gib']:.1f} GiB" if u["wall_s"] else ""))
    print("average rank, time: " + ", ".join(f"{c} {r:.2f}" for c, r in sorted(s["average_rank_time"].items(), key=lambda kv: kv[1])))
    print("average rank, space: " + ", ".join(f"{c} {r:.2f}" for c, r in sorted(s["average_rank_space"].items(), key=lambda kv: kv[1])))
    for t in s["time_tests"] + s["space_tests"]:
        print(f"  {t['comparison']}: n={t['n']} shapiro={t['shapiro']:.3f} wilcoxon={t['wilcoxon']:.3f} r={t['r']:.3f} ({t['label']})")
    print(f"fragments in {args.out}")


if __name__ == "__main__":
    main()
