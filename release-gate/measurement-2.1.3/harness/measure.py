"""Run each evaluation script with plain Python and under each `now run` configuration of the
evaluation, from a fresh copy each time, and record what each run computed.

usage: python measure.py OUTDIR [--only s11,s2] [--workers 4] [--reduced]
Writes OUTDIR/<sid>/<config>.json; compare.py reads them. A run already recorded is skipped.
"""

import argparse
import concurrent.futures as cf
import sys
import hashlib
import json
import os
import pathlib
import signal
import subprocess
import tempfile
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "src"
VENV = HERE / "venv213" / "bin"
HOOK = HERE / "hook"
RETRY_CAPPED = False
TIMEOUT = 30 * 60

# id, folder, arguments (run.sh of noworkflow-overhead-experiments; ids of the paper's table)
SCRIPTS = [
    ("s1", "03dataoneexps/03dataoneexps_exp01_32_Accessing_Hydrologic_Data", "main.py"),
    ("s2", "03dataoneexps/03dataoneexps_exp03_46_A_Method_For_Calculating", "main.py"),
    ("s3", "03dataoneexps/03dataoneexps_exp04_49_Analysis_Of_Flow", "main.py"),
    ("s4", "03dataoneexps/03dataoneexps_exp02_40_e_44_Agua_Salud_Rainfall_Data", "export_rainfall.py --site MOS -d gage_data --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z"),
    ("s5", "03dataoneexps/03dataoneexps_exp05_37_Agua_Salud_Discharge_Data", "export_discharge.py --site FOR -d discharge_sharp --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z"),
    ("s6", "05msrgithubexps/05msrgithubexps_exp02_cvar", "cvar.py 500"),
    ("s7", "05msrgithubexps/05msrgithubexps_exp03_eq_solver", "eq_solver.py 500"),
    ("s8", "05msrgithubexps/05msrgithubexps_exp04_curves", "curves.py 5000 5000 5000 5000 5000 5000 5000 5000"),
    ("s9", "05msrgithubexps/05msrgithubexps_exp05_chunks", "chunks.py 500"),
    ("s10", "05msrgithubexps/05msrgithubexps_exp07_median", "median.py 500"),
    ("s11", "05msrgithubexps/05msrgithubexps_exp06_find_gc", "gc.py CR954253.fasta"),
    ("s12", "05msrgithubexps/05msrgithubexps_exp01_mov_robots", "mov_robots.py"),
    ("s13", "04benchproglangs/04benchpl_exp09_iterative_solver_jacobi_OK", "test_laplace_jacobi2.py 105"),
    ("s14", "menger-sponge", "menger_sponge2.py"),
    ("s15", "04benchproglangs/04benchpl_exp06_belief_propagation_OK", "test_belief_propagation.py 20000"),
    ("s16", "04benchproglangs/04benchpl_exp08_fft_OK", "test_compute_FFT.py 20000"),
    ("s17", "04benchproglangs/04benchpl_exp10_square_root_matrix_OK", "test_sqrt_matrix.py 6000"),
    ("s18", "04benchproglangs/04benchpl_exp11_gauss_legendre_quadrature_OK", "gauss_legendre_quadrature_py3.py 10000"),
    ("s19", "04benchproglangs/04benchpl_exp12_function_evaluation_OK", "test_evaluate_functions.py 80000"),
    ("s20", "04benchproglangs/04benchpl_exp07_metropolis_hastings", "metropolis_hastings.py 27000000"),
    ("s21", "04benchproglangs/04benchpl_exp14_pernicious_numbers_OK", "test_pernicious_numbers.py 20000000"),
]
# Did not finish within 30 minutes under any noWorkflow configuration in the evaluation:
# measured on a reduced input instead (not a configuration the paper reports).
REDUCED = {
    "s14": ("menger_sponge2.py", ("n = 6500", "n = 150")),
    "s20": ("metropolis_hastings.py 20000", None),
    "s21": ("test_pernicious_numbers.py 20000", None),
}
CONFIGS = {
    "python": [],
    "python-control": [],
    "now": ["now", "run"],
    "d2": ["now", "run", "-d", "2"],
    "d3": ["now", "run", "-d", "3"],
    "cg": ["now", "run", "-cg"],
    "cg-d2": ["now", "run", "-cg", "-d", "2"],
    "cg-d3": ["now", "run", "-cg", "-d", "3"],
    "e-none": ["now", "run", "-e", "none"],
    "e-relevant": ["now", "run", "-e", "relevant"],
}
# s2 under the unlimited configurations writes a store of about 22 GiB: one at a time.
HEAVY = {("s2", c) for c in ("now", "d3", "cg", "cg-d3")}
# A run whose processes hold more than this (resident) is killed and recorded as
# "memory-cap": noWorkflow keeps the provenance in memory until the end, and two
# kernel panics of a 16 GB Mac came from that.
CAP = {"heavy": 64 << 30, "light": 24 << 30}
# Linux: a run that holds more than FLOOR_RUN is killed (and recorded as "memory-cap")
# when the machine's available memory falls below FLOOR, so that a shared machine never
# runs dry; rerun those alone with --retry-capped --workers 1.
FLOOR, FLOOR_RUN = 16 << 30, 4 << 30


def available():
    """MemAvailable of the machine, or None off Linux"""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        return None
    return None


def tree_rss(pid):
    """Resident bytes of the processes of the session ``pid`` leads"""
    if sys.platform == "linux":
        total = 0
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/stat") as f:
                    fields = f.read().rsplit(")", 1)[1].split()
                if int(fields[3]) != pid:  # session id
                    continue
                with open(f"/proc/{entry}/statm") as f:
                    total += int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
            except (OSError, IndexError, ValueError):
                continue
        return total
    out = subprocess.run(["ps", "-o", "rss=", "-g", str(pid)], capture_output=True, text=True).stdout
    return sum(int(x) for x in out.split()) * 1024


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one(outdir, sid, folder, args, config, patch, cap):
    out = outdir / sid / f"{config}.json"
    if out.exists():
        if not (RETRY_CAPPED and json.loads(out.read_text())["status"] == "memory-cap"):
            return sid, config, "cached"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"m-{sid}-{config}-", dir=HERE / "runs") as tmp:
        work = pathlib.Path(tmp) / "w"
        clone = ["cp", "-cR"] if sys.platform == "darwin" else ["cp", "-a", "--reflink=auto"]
        subprocess.run(clone + [str(SRC / folder), str(work)], check=True)
        if patch:
            script = work / args.split()[0]
            script.write_text(script.read_text().replace(*patch))
        digests = pathlib.Path(tmp) / "digests.json"
        env = dict(os.environ, PYTHONPATH=str(HOOK), MIRROR_OUT=str(digests), MIRROR_DIR=str(work),
                   MPLBACKEND="Agg", PYTHONHASHSEED="0", PATH=f"{VENV}:{os.environ['PATH']}")
        env.pop("VIRTUAL_ENV", None)
        prefix = CONFIGS[config]
        cmd = ([str(VENV / "python")] if not prefix else [str(VENV / "now")] + prefix[1:]) + args.split()
        start = time.monotonic()
        proc = subprocess.Popen(cmd, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        peak, over = 0, []

        def watch():
            nonlocal peak
            while proc.poll() is None:
                rss = tree_rss(proc.pid)
                peak = max(peak, rss)
                free = available()
                if rss > cap or (free is not None and free < FLOOR and rss > FLOOR_RUN):
                    over.append(rss)
                    os.killpg(proc.pid, signal.SIGKILL)
                    return
                time.sleep(1)

        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        try:
            so, se = proc.communicate(timeout=TIMEOUT)
            status = proc.returncode
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            so, se = proc.communicate()
            status = "timeout"
        watcher.join()
        if over:
            status = "memory-cap"
        elapsed = time.monotonic() - start
        files = {}
        store = 0
        for p in sorted(work.rglob("*")):
            rel = p.relative_to(work).as_posix()
            if rel == ".noworkflow" or rel.startswith(".noworkflow/"):
                if p.is_file():
                    store += p.stat().st_size
                continue
            if p.is_file():
                files[rel] = sha1(p)
        record = {
            "sid": sid, "config": config, "cmd": " ".join(cmd[1:] if prefix else ["python"] + args.split()),
            "status": status, "elapsed": elapsed, "store_bytes": store, "peak_rss": peak,
            "platform": sys.platform,
            "stdout": so.decode(errors="replace"), "stderr": se.decode(errors="replace")[-4000:],
            "files": files,
            "digests": json.loads(digests.read_text()) if digests.exists() else None,
        }
        out.write_text(json.dumps(record, indent=1))
        return sid, config, f"{status} {elapsed:.1f}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--only")
    ap.add_argument("--configs")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--reduced", action="store_true", help="only the reduced inputs of s14, s20, s21")
    ap.add_argument("--retry-capped", action="store_true", help="run again what a memory cap killed")
    ap.add_argument("--cap", type=int, help="GiB: the memory cap of every run, instead of CAP")
    a = ap.parse_args()
    if a.cap:
        CAP.update(heavy=a.cap << 30, light=a.cap << 30)
    global RETRY_CAPPED
    RETRY_CAPPED = a.retry_capped
    outdir = pathlib.Path(a.outdir).resolve()
    (HERE / "runs").mkdir(exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    configs = a.configs.split(",") if a.configs else list(CONFIGS)
    jobs = []
    for sid, folder, args in SCRIPTS:
        if only and sid not in only:
            continue
        patch = None
        if a.reduced:
            if sid not in REDUCED:
                continue
            args, patch = REDUCED[sid]
        for config in configs:
            if not a.reduced and sid in REDUCED and config not in ("python", "python-control"):
                continue
            jobs.append((sid, folder, args, config, patch))
    heavy = [j for j in jobs if (j[0], j[3]) in HEAVY]
    light = [j for j in jobs if (j[0], j[3]) not in HEAVY]
    # the long cells first, so that the pool does not end on one of them
    light.sort(key=lambda j: j[0] not in ("s13", "s15", "s19"))
    lock = threading.Lock()

    def report(fut):
        with lock:
            print(*fut.result(), flush=True)

    with cf.ThreadPoolExecutor(1) as hp, cf.ThreadPoolExecutor(a.workers) as lp:
        futs = [hp.submit(run_one, outdir, *j, CAP["heavy"]) for j in heavy]
        futs += [lp.submit(run_one, outdir, *j, CAP["light"]) for j in light]
        for f in futs:
            f.add_done_callback(report)
        cf.wait(futs)
        for f in futs:
            f.result()


if __name__ == "__main__":
    main()
