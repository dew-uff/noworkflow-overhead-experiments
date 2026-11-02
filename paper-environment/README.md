# The environment of the paper's noWorkflow executions

Every execution of noWorkflow that the paper reports or shows ran on the
machine of its overhead evaluation (Section 7.3 of the paper), on Python
3.12.15, in one environment, recorded here with every version pinned:

- `measurement.txt`: `pip freeze` of the virtual environment of the release
  gate of noWorkflow 2.2.0 (`../release-gate/results/2.2.0-ca5c198cde13/`),
  in which the 21 scripts of the overhead evaluation and the three trials of
  the "Beyond Python" case study were timed. Its noWorkflow is the wheel of
  the release, the same file PyPI serves (sha256 `ca5c198c…`, in
  `candidate.json` next to the results).
- `requirements.txt`: the same versions plus scikit-learn and
  imbalanced-learn, and what they pull in, which the running example of the
  paper imports and none of the 21 scripts does; resolved with
  `measurement.txt` as constraints, so that no shared version differs. This
  is the environment in which the trial histories of the running example and
  of the case study were rebuilt from the reproducibility package
  [`dew-uff/noworkflow-analysis`](https://github.com/dew-uff/noworkflow-analysis)
  (tag `is-2026-r1`) to produce the listings and figures of the paper:

  ```bash
  pip install -r requirements.txt
  ```

The versions were resolved on Linux x86_64 (Ubuntu 26.04.1, kernel 7.0), with
`uv pip compile` over `requirements.in`. On the machine, R 4.5.2 with rdtLite
1.4, gcc 15.2.0, strace 6.19 and Graphviz 14.1.2 were installed.
