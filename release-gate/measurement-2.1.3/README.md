# The 21 scripts under noWorkflow 2.1.3, compared with plain Python

The measurement that led to the release gate (`../README.md`), kept as it ran: its harness,
unchanged, and its 216 results. The findings are in
[gems-uff/noworkflow#467](https://github.com/gems-uff/noworkflow/issues/467): under `-d 2`, s4,
s5, s11 and s12 compute something other than plain Python, with status 0
([#243](https://github.com/gems-uff/noworkflow/issues/243), fixed for 2.2.0), and s19 holds
36.5 GiB under the configurations without a depth limit.

- **When and where**: 2026-10-24, Ubuntu 24.04 on an Intel i9-14900KF with 128 GB, Python
  3.12.3, numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, noWorkflow 2.1.3 from PyPI, the scripts of
  this repository at `078a892`. Several runs shared the machine at once: the times here are
  not overhead figures.
- **What a run is compared on**: its return code, its stdout (an elapsed time on the last
  line masked), the SHA-1 of every file it leaves (the store excluded), and the digests of
  what each function of the script returned and of the final globals, which
  `harness/hook/sitecustomize.py` records through `sys.monitoring`. Plain Python runs twice,
  and what the two runs disagree on is left out.
- **Limits**: 30 minutes per run, as in the paper's evaluation. s14, s20 and s21 ran with the
  original input under plain Python only, and under noWorkflow with a reduced one
  (`results/reduced/`): `menger_sponge2.py` with n = 150, `metropolis_hastings.py 20000`,
  `test_pernicious_numbers.py 20000`.

`harness/` holds `measure.py` (runs, one JSON per script and configuration), `compare.py`
(the verdicts: `python3 harness/compare.py results/full --verbose`) and the hook. Its paths
(`src/`, `venv213/`) were those of the machine; in the results, the run directory reads
`<run>` and the harness directory `<harness>`.

## What this harness got wrong, and the gate does not

Its hook called back into Python on every start and every return of every function of the
script, and hashed the running digest again each time. On scripts of hundreds of millions of
calls that costs more than the script: `results/full/s14/python.json` and
`results/full/s21/python.json` end in `timeout` under **plain Python**, which the paper's
evaluation ran in 485 s and 62 s. On `test_pernicious_numbers.py 300000` the hook took a run
from 0.15 s to 42.7 s, 280 times, which is enough to explain both. The gate's hook digests the first 100,000 returns of each function and
then stops listening, which bounds its cost (2.4 s on the same run, 3.9 s on ten times the
input), and keeps the start event for the top level only.
