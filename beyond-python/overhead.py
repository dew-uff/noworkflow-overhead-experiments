"""Overhead of the Beyond Python case study: the three trials of run.sh
without noWorkflow, with `now run --external-tracer none` and with
`now run` (argv, the default). Fresh directory per repetition and
configuration, order of the configurations rotated per repetition.

usage: overhead.py <checkout> <analysis>/beyond-python <dataset> <workdir> [reps]
"""
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import time

checkout, case, dataset, work = sys.argv[1:5]
reps = int(sys.argv[5]) if len(sys.argv) > 5 else 3
py = os.path.join(checkout, ".venv/bin/python")
now = os.path.join(checkout, ".venv/bin/now")
CFGS = {
    "plain": [py, "fraud_pipeline.py"],
    "none": [now, "run", "--external-tracer", "none", "fraud_pipeline.py"],
    "argv": [now, "run", "fraud_pipeline.py"],
}
PATCHES = [None, "patch_2_threshold.patch", "patch_3_accuracy.patch"]


def du(path):
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            total += os.path.getsize(os.path.join(root, name))
    return total


results = []
names = list(CFGS)
for rep in range(1, reps + 1):
    order = names[rep - 1:] + names[:rep - 1]
    for cfg in order:
        d = os.path.join(work, f"r{rep}-{cfg}")
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        for f in ("fraud_pipeline.py", "model.R", "metrics.c"):
            shutil.copy(os.path.join(case, f), d)
        shutil.copy(dataset, os.path.join(d, "creditcard.csv"))
        for t, patch in enumerate(PATCHES, 1):
            if patch:
                with open(os.path.join(case, patch), "rb") as p:
                    subprocess.run(["patch", "-s", "-p1"], stdin=p, cwd=d, check=True)
            for out in ("pred.csv", "out.txt", "metrics"):
                if os.path.exists(os.path.join(d, out)):
                    os.remove(os.path.join(d, out))
            start = time.perf_counter()
            proc = subprocess.run(CFGS[cfg], cwd=d, capture_output=True, text=True)
            wall = time.perf_counter() - start
            with open(os.path.join(d, "out.txt"), "rb") as o:
                digest = hashlib.sha1(o.read()).hexdigest()
            row = {"rep": rep, "cfg": cfg, "trial": t, "wall": round(wall, 3),
                   "status": proc.returncode, "out_sha1": digest,
                   "stderr_tail": proc.stderr.strip().splitlines()[-1:]}
            results.append(row)
            print(json.dumps(row), flush=True)
        store = os.path.join(d, ".noworkflow")
        size = du(store) if os.path.isdir(store) else 0
        results.append({"rep": rep, "cfg": cfg, "store_bytes": size})
        print(json.dumps(results[-1]), flush=True)
        shutil.rmtree(d)

with open(os.path.join(work, "results.json"), "w") as f:
    json.dump(results, f, indent=1)

runs = [r for r in results if "wall" in r]
print("\ncfg    median T1/T2/T3 (s)        median of the sum (s)  vs plain")
base = None
for cfg in names:
    per = [statistics.median(r["wall"] for r in runs if r["cfg"] == cfg and r["trial"] == t) for t in (1, 2, 3)]
    sums = [sum(r["wall"] for r in runs if r["cfg"] == cfg and r["rep"] == rep) for rep in range(1, reps + 1)]
    med = statistics.median(sums)
    base = base or med
    print(f"{cfg:6} {per[0]:7.2f} {per[1]:7.2f} {per[2]:7.2f}   {med:8.2f} (min {min(sums):.2f}, max {max(sums):.2f})  {100 * (med / base - 1):+.1f}%")
print("statuses:", sorted({r["status"] for r in runs}), "out.txt digests per trial:",
      {t: sorted({r["out_sha1"][:10] for r in runs if r["trial"] == t}) for t in (1, 2, 3)})
print("store bytes:", {r["cfg"]: r["store_bytes"] for r in results if "store_bytes" in r})
