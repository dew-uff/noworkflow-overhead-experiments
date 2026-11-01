"""Time of the fourth trial of the Beyond Python case study, model.R under
rdtLite, and of the R step it changes: the trial under `now run` with the
wrapper of rdtlite/, which runs model.R through rdtLite's prov.run
(`trial4`), the same wrapper under plain Python (`trial4-plain`), which
separates the cost of rdtLite from the cost of noWorkflow, and the R step
alone, without noWorkflow, as `Rscript model.R` (`r`) and through prov.run
(`r-rdtlite`). The same trial without rdtLite is the first trial of
overhead.py. Fresh directory per repetition and measure, order of the
measures rotated per repetition.

<venv> is an environment with the noWorkflow under measurement and pandas;
R needs the rdtLite package.

usage: rdtlite_time.py <venv> <analysis>/beyond-python <dataset> <workdir> [reps]
"""
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import time

venv, case, dataset, work = sys.argv[1:5]
reps = int(sys.argv[5]) if len(sys.argv) > 5 else 3
py = os.path.join(venv, "bin/python")
now = os.path.join(venv, "bin/now")
SOURCES = {"fraud_pipeline.py": "rdtlite/fraud_pipeline.py", "model.R": "model.R", "metrics.c": "metrics.c"}
# measure: (command, files of the case, input, output whose digest is kept)
MEASURES = {
    "trial4": ([now, "run", "fraud_pipeline.py"], ("fraud_pipeline.py", "model.R", "metrics.c"), "creditcard.csv", "out.txt"),
    "trial4-plain": ([py, "fraud_pipeline.py"], ("fraud_pipeline.py", "model.R", "metrics.c"), "creditcard.csv", "out.txt"),
    "r": (["Rscript", "model.R", "prepared.csv", "pred.csv"], ("model.R",), "prepared.csv", "pred.csv"),
    "r-rdtlite": (["Rscript", "-e", 'rdtLite::prov.run("model.R", prov.dir = ".")'], ("model.R",), "prepared.csv", "pred.csv"),
}


def du(path):
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            total += os.path.getsize(os.path.join(root, name))
    return total


def sha1(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


# The input of the R step, made once as the wrapper's prepare() makes it, and not timed.
os.makedirs(work, exist_ok=True)
prepared = os.path.join(work, "prepared.csv")
subprocess.run([py, "-c", "import sys, pandas as pd; "
                "pd.read_csv(sys.argv[1], encoding='utf-8').drop(columns=['Time']).to_csv(sys.argv[2], index=False)",
                dataset, prepared], check=True)

results = []
names = list(MEASURES)
for rep in range(1, reps + 1):
    k = (rep - 1) % len(names)
    for m in names[k:] + names[:k]:
        cmd, files, given, out = MEASURES[m]
        d = os.path.join(work, f"r{rep}-{m}")
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        for f in files:
            shutil.copy(os.path.join(case, SOURCES[f]), os.path.join(d, f))
        shutil.copy(dataset if given == "creditcard.csv" else prepared, os.path.join(d, given))
        start = time.perf_counter()
        proc = subprocess.run(cmd, cwd=d, capture_output=True, text=True)
        wall = time.perf_counter() - start
        row = {"rep": rep, "measure": m, "wall": round(wall, 3), "status": proc.returncode,
               "out": out, "out_sha1": sha1(os.path.join(d, out)),
               "stderr_tail": proc.stderr.strip().splitlines()[-1:]}
        if m == "trial4":
            store = os.path.join(d, ".noworkflow")
            row["store_bytes"] = du(store) if os.path.isdir(store) else 0
        results.append(row)
        print(json.dumps(row), flush=True)
        shutil.rmtree(d)
os.remove(prepared)

with open(os.path.join(work, "results.json"), "w") as f:
    json.dump(results, f, indent=1)

print("\nmeasure     median (s)  min-max (s)")
for m in names:
    walls = [r["wall"] for r in results if r["measure"] == m]
    print(f"{m:10} {statistics.median(walls):9.2f}  {min(walls):.2f}-{max(walls):.2f}")
print("statuses:", sorted({r["status"] for r in results}), "digests:",
      {m: sorted({(r["out_sha1"] or "-")[:10] for r in results if r["measure"] == m}) for m in names})
