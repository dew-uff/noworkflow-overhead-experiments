"""The release gate of noWorkflow (gems-uff/noworkflow#469): the paper's evaluation, run on one
candidate wheel, stopping at the first run that computes something other than plain Python.

  python3 gate.py correctness RESULTS --env ENV [--workers 6] [--budget 110] [--only s1,s2] [--configs now,d2]
  python3 gate.py timing RESULTS --env ENV [--repetitions 10] [--retries 2] [--only ...] [--configs ...]

ENV is what setup.py made for the candidate. RESULTS gets correctness/ and timing/, one JSON per
run; a run already recorded is skipped, so the same command resumes a pass, on the same
candidate only. The exit status is 0 for a clean pass, 1 when a run differs from plain Python
(RESULTS/<pass>/STOP.json says which and how), 2 for anything else.

Correctness: plain Python twice (the second run is the control for nondeterminism) and the
eight configurations, from fresh copies, in parallel within a memory budget; the scripts of
scripts.ALONE run under noWorkflow with nothing beside them, and a run the memory cap kills
while others ran is run again alone. A run is compared on its status, its stdout (the elapsed
time it prints last is masked), the SHA-1 of every file it leaves and the digests of what each
function of the script returned and of the final globals (hook/sitecustomize.py).

Timing: only after a clean correctness pass of the same candidate; one run at a time, plain
Python and the eight configurations, the order of the configurations rotated in each
repetition. Each run is compared with the plain run of the correctness pass on status, stdout
and files (the hook only seeds: its digests would weigh on the times). On a machine prepared
by prepare.py the runs are pinned to its run CPU and the harness to its own; interference
(other work, the run CPU's frequency, throttling) is recorded with each run, and a disturbed
run is repeated, up to --retries more times.

No run is ever interrupted for its duration. A run that the kernel kills for memory (the cap
of the unit prepare.py launches) is a result, "oom", recorded and not repeated.
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compare  # noqa: E402
import prepare  # noqa: E402
from scripts import ALONE, CONFIGS, DEFAULT_PEAK_GIB, PEAK_GIB, PLAIN, SCRIPTS  # noqa: E402

HOOK = HERE / "hook"
# Fixed thread counts of the numerical libraries: every run gets one CPU in the timing pass,
# and the same in both passes.
THREADS = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                            "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS")}
# The long runs of the correctness pass start first, so that the pool does not end on one.
LONG = ("s2", "s13", "s15", "s3")
# When a timing run counts as disturbed (each threshold is recorded with the run, and the
# samples it was judged on, so that the analysis can apply another).
DISTURBED = {
    "foreign_on_run_cpu_fraction": 0.01,  # CPU time on the run CPU that was not the run's, over the wall time
    "foreign_on_run_cpu_floor_s": 0.1,
    "others_cpus_mean": 0.5,  # CPUs busy elsewhere (not the run CPU, not the harness CPU), on average
    "frequency_tolerance": 0.02,  # median frequency of the run CPU against its maximum after the preparation
}
SAMPLE_S = 1.0
SCAN_EVERY = 5  # samples between two scans of every process (who else is using the machine)
EXIT_DIFFERS, EXIT_ERROR = 1, 2


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def log(*args):
    print(utcnow(), *args, flush=True)


def digest_file(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(data, indent=1))
    tmp.replace(path)


# ---------------------------------------------------------------- /proc (Linux)


def tree_rss(pid):
    """Resident bytes of the processes of the session pid leads"""
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
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-g", str(pid)], capture_output=True, text=True).stdout
    except OSError:  # a sandbox that forbids ps: the peak is then the run's own ru_maxrss
        return 0
    return sum(int(x) for x in out.split()) * 1024


def oom_kills():
    """How many processes the kernel killed for memory in this process's cgroup, or None"""
    try:
        path = pathlib.Path("/proc/self/cgroup").read_text().strip().split("::", 1)[1]
        for line in pathlib.Path(f"/sys/fs/cgroup{path}/memory.events").read_text().splitlines():
            if line.startswith("oom_kill "):
                return int(line.split()[1])
    except (OSError, IndexError, ValueError):
        pass
    return None


def cpu_times():
    """{cpu: (busy, total)} in clock ticks, from /proc/stat"""
    out = {}
    with open("/proc/stat") as f:
        for line in f:
            if line.startswith("cpu") and line[3].isdigit():
                name, *vals = line.split()
                vals = [int(v) for v in vals[:8]]  # user nice system idle iowait irq softirq steal
                out[int(name[3:])] = (sum(vals) - vals[3] - vals[4], sum(vals))
    return out


def processes(exclude_session, exclude_pid):
    """{pid: (who, comm, ticks)} of every process but the run's session and the harness"""
    me, out = os.getuid(), {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit() or int(entry) == exclude_pid:
            continue
        try:
            with open(f"/proc/{entry}/stat") as f:
                head, tail = f.read().rsplit(")", 1)
            fields = tail.split()
            if int(fields[3]) == exclude_session:
                continue
            uid = os.stat(f"/proc/{entry}").st_uid
        except (OSError, IndexError, ValueError):
            continue
        who = "root" if uid == 0 else "self" if uid == me else "other"  # the results are public: no names
        out[int(entry)] = (who, head.split("(", 1)[1], int(fields[11]) + int(fields[12]))
    return out


def throttles(cpu):
    base = pathlib.Path(f"/sys/devices/system/cpu/cpu{cpu}/thermal_throttle")
    return {k: int(prepare.read(base / f"{k}_throttle_count", "0")) for k in ("core", "package")}


def package_temp():
    best = None
    for zone in pathlib.Path("/sys/class/thermal").glob("thermal_zone*"):
        if prepare.read(zone / "type") == "x86_pkg_temp":
            t = prepare.read(zone / "temp")
            if t:
                best = max(best or 0, int(t) / 1000)
    return best


class Sampler(threading.Thread):
    """Samples a run every second: its resident memory and, in the timing pass on Linux, what
    else the machine does."""

    def __init__(self, pid, rss_cap=None, run_cpu=None, harness_cpu=None):
        super().__init__(daemon=True)
        self.pid, self.rss_cap, self.run_cpu, self.harness_cpu = pid, rss_cap, run_cpu, harness_cpu
        self.watch = run_cpu is not None and sys.platform == "linux"
        self.finished = threading.Event()
        self.peak, self.capped, self.error = 0, False, None
        self.freqs, self.temps, self.others = [], [], []
        self.top = {}
        if self.watch:
            self.cpu0, self.throttle0 = cpu_times(), throttles(run_cpu)
            self.nominal = prepare.read(f"/sys/devices/system/cpu/cpu{run_cpu}/cpufreq/scaling_max_freq")
            self.procs = processes(pid, os.getpid())

    def run(self):
        try:
            self.sample()
        except Exception as exc:  # noqa: BLE001 (a sampler that dies must not go unnoticed)
            self.error = repr(exc)

    def sample(self):
        n, last = 0, self.cpu0 if self.watch else None
        while not self.finished.wait(SAMPLE_S):
            rss = tree_rss(self.pid)
            self.peak = max(self.peak, rss)
            if self.rss_cap and rss > self.rss_cap:
                self.capped = True
                try:
                    os.killpg(self.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                return
            if not self.watch:
                continue
            n += 1
            now = cpu_times()
            busy = sum(now[c][0] - last[c][0] for c in now if c in last and c not in (self.run_cpu, self.harness_cpu))
            self.others.append(busy / os.sysconf("SC_CLK_TCK") / SAMPLE_S)
            last = now
            f = prepare.read(f"/sys/devices/system/cpu/cpu{self.run_cpu}/cpufreq/scaling_cur_freq")
            if f:
                self.freqs.append(int(f))
            t = package_temp()
            if t is not None:
                self.temps.append(t)
            if n % SCAN_EVERY == 0:
                procs = processes(self.pid, os.getpid())
                for pid, (who, comm, ticks) in procs.items():
                    before = self.procs.get(pid)
                    used = ticks - (before[2] if before and before[:2] == (who, comm) else 0)
                    if used > 0:
                        key = f"{who}:{comm}"
                        self.top[key] = self.top.get(key, 0) + used
                self.procs = procs

    def summary(self, rusage, wall):
        """What the run met, and the reasons it counts as disturbed (empty: it does not)"""
        if not self.watch:
            return None, []
        hz = os.sysconf("SC_CLK_TCK")
        busy_run_cpu = (cpu_times()[self.run_cpu][0] - self.cpu0[self.run_cpu][0]) / hz
        foreign = busy_run_cpu - (rusage.ru_utime + rusage.ru_stime)
        throttle = {k: v - self.throttle0[k] for k, v in throttles(self.run_cpu).items()}
        freqs = sorted(self.freqs)
        s = {
            "run_cpu": self.run_cpu, "harness_cpu": self.harness_cpu, "samples": len(self.others),
            "nominal_khz": int(self.nominal) if self.nominal else None,
            "freq_khz": {"min": freqs[0], "median": freqs[len(freqs) // 2], "max": freqs[-1]} if freqs else None,
            "temp_c_max": max(self.temps) if self.temps else None,
            "throttle": throttle,
            "others_cpus": {"mean": sum(self.others) / len(self.others), "max": max(self.others)} if self.others else None,
            "foreign_on_run_cpu_s": round(foreign, 3),
            "top_others": sorted(((k, round(v / hz, 2)) for k, v in self.top.items()), key=lambda kv: -kv[1])[:5],
            "thresholds": DISTURBED,
        }
        reasons = []
        if any(throttle.values()):
            reasons.append(f"throttled {throttle}")
        if foreign > max(DISTURBED["foreign_on_run_cpu_floor_s"], DISTURBED["foreign_on_run_cpu_fraction"] * wall):
            reasons.append(f"{foreign:.2f}s of other work on the run CPU")
        if s["others_cpus"] and s["others_cpus"]["mean"] > DISTURBED["others_cpus_mean"]:
            reasons.append(f"{s['others_cpus']['mean']:.2f} CPUs busy elsewhere on average")
        if s["freq_khz"] and s["nominal_khz"]:
            off = abs(s["freq_khz"]["median"] - s["nominal_khz"]) / s["nominal_khz"]
            if off > DISTURBED["frequency_tolerance"]:
                reasons.append(f"run CPU at {s['freq_khz']['median']} kHz, not {s['nominal_khz']}")
        return s, reasons


# ---------------------------------------------------------------- the gate


class Job:
    def __init__(self, sid, folder, args, config, alone=False):
        self.sid, self.folder, self.args, self.config, self.alone = sid, folder, args, config, alone
        self.peak = PEAK_GIB.get(sid, DEFAULT_PEAK_GIB)

    def __repr__(self):
        return f"{self.sid} {self.config}"


class Stop(Exception):
    pass


class Gate:
    def __init__(self, a, pass_):
        self.pass_ = pass_
        self.env_dir = pathlib.Path(a.env).resolve()
        self.bin = self.env_dir / "venv" / "bin"
        self.src = self.env_dir / "src"
        self.results = pathlib.Path(a.results).resolve()
        self.pdir = self.results / pass_
        self.work = pathlib.Path(a.workdir).resolve() if a.workdir else self.env_dir / "runs"
        self.work.mkdir(parents=True, exist_ok=True)
        self.rss_cap = a.rss_cap << 30 if a.rss_cap else None
        self.only = set(a.only.split(",")) if a.only else None
        self.configs = a.configs.split(",") if a.configs else [c for c in CONFIGS if c not in PLAIN]
        unknown = [c for c in self.configs if c not in CONFIGS or c in PLAIN]
        if unknown:
            raise SystemExit(f"unknown configurations: {unknown}")
        self.scripts = [s for s in SCRIPTS if not self.only or s[0] in self.only]
        self.complete = not self.only and set(self.configs) == set(CONFIGS) - set(PLAIN)
        self.stopping = threading.Event()
        self.lock = threading.Lock()
        self.running = {}
        self.candidate = self.check_candidate()
        self.prep = prepare.state() if sys.platform == "linux" else None

    def check_candidate(self):
        rec = json.loads((self.env_dir / "env.json").read_text())
        if digest_file(self.env_dir / rec["wheel"], "sha256") != rec["sha256"]:
            raise SystemExit(f"{rec['wheel']} no longer has the sha256 setup.py recorded")
        out = subprocess.run([str(self.bin / "now"), "--version"], capture_output=True, text=True)
        if (out.stdout + out.stderr).strip() != rec["version"]:
            raise SystemExit("the venv's `now --version` is not what setup.py recorded")
        cand = {k: rec[k] for k in ("wheel", "sha256", "version", "python", "scripts_commit", "scripts_dirty")}
        path = self.results / "candidate.json"
        if path.exists():
            before = json.loads(path.read_text())
            if before["sha256"] != cand["sha256"]:
                raise SystemExit(f"{self.results} holds results of {before['wheel']} ({before['sha256'][:12]}): "
                                 "a new candidate starts in a new directory")
        else:
            write_json(path, cand)
        return cand

    def record_machine(self):
        write_json(self.pdir / f"machine-{utcnow().replace(':', '')}.json", {
            "pass": self.pass_, "started_at": utcnow(), "candidate": self.candidate,
            "machine": prepare.describe(), "preparation": self.prep, "threads": THREADS,
            "freeze": [self.scrub(x) for x in json.loads((self.env_dir / "env.json").read_text())["freeze"]],
            "argv": [self.scrub(x) for x in sys.argv[1:]],
        })

    def scrub(self, text, *dirs):
        """text without the absolute paths of this machine: the results are public, and the
        directory of each run has its own name"""
        for d, name in [(x, "<run>") for x in dirs] + [(self.env_dir, "<env>"), (self.results, "<results>"),
                                                     (pathlib.Path.home(), "~")]:
            for form in {str(d), os.path.realpath(d)}:
                text = text.replace(form, name)
        return text

    def run_env(self, work, digests, deep):
        env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH")}
        env.update(THREADS)
        env.update(PYTHONPATH=str(HOOK), MIRROR_OUT=str(digests), MIRROR_DIR=str(work),
                   MIRROR_MODE="full" if deep else "seed", MPLBACKEND="Agg", PYTHONHASHSEED="0",
                   PATH=f"{self.bin}{os.pathsep}{env.get('PATH', '')}")
        return env

    def run_one(self, job, deep, pin=None):
        """Run job once from a fresh copy; the record of what it computed and cost"""
        tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"{job.sid}-{job.config}-", dir=self.work))
        try:
            work = tmp / "w"
            clone = ["cp", "-cR"] if sys.platform == "darwin" else ["cp", "-a", "--reflink=auto"]
            subprocess.run(clone + [str(self.src / job.folder), str(work)], check=True)
            digests = tmp / "digests.json"
            flags = CONFIGS[job.config]
            shown = (["now", *flags] if flags else ["python"]) + job.args.split()
            cmd = [str(self.bin / ("now" if flags else "python"))] + shown[1:]
            if pin is not None and sys.platform == "linux":
                cmd = ["taskset", "-c", str(pin)] + cmd
            oom0 = oom_kills()
            started = utcnow()
            with open(tmp / "stdout", "wb") as out, open(tmp / "stderr", "wb") as err:
                t0 = time.monotonic()
                proc = subprocess.Popen(cmd, cwd=work, env=self.run_env(work, digests, deep), stdin=subprocess.DEVNULL,
                                        stdout=out, stderr=err, start_new_session=True)
                with self.lock:
                    self.running[proc.pid] = job
                sampler = Sampler(proc.pid, self.rss_cap, *((pin, self.prep["harness_cpu"]) if pin is not None and self.prep else (pin, None)))
                sampler.start()
                _, wstatus, rusage = os.wait4(proc.pid, 0)
                wall = time.monotonic() - t0
            proc.returncode = os.waitstatus_to_exitcode(wstatus)
            sampler.finished.set()
            sampler.join()
            with self.lock:
                self.running.pop(proc.pid, None)
            try:  # whatever the script left running
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            code = proc.returncode
            if code >= 0:
                status = code
            elif self.stopping.is_set():
                status = "stopped"
            elif sampler.capped:
                status = "memory-cap"
            elif -code == signal.SIGKILL and oom0 is not None and (oom_kills() or 0) > oom0:
                status = "oom"
            else:
                status = f"signal {-code}"
            interference, reasons = sampler.summary(rusage, wall)
            maxrss = rusage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
            files, store, store_disk = {}, 0, 0
            for p in sorted(work.rglob("*")):
                rel = p.relative_to(work).as_posix()
                if rel == ".noworkflow" or rel.startswith(".noworkflow/"):
                    if p.is_file() and not p.is_symlink():
                        st = p.stat()
                        store += st.st_size
                        store_disk += st.st_blocks * 512
                    continue
                if p.is_file():
                    files[rel] = digest_file(p, "sha1")
            stdout = self.scrub((tmp / "stdout").read_bytes().decode(errors="replace"), work, tmp)
            return {
                "sid": job.sid, "config": job.config, "cmd": " ".join(shown), "status": status,
                "wall": wall, "reported": compare.reported(stdout),
                "user": rusage.ru_utime, "sys": rusage.ru_stime, "peak_rss": max(sampler.peak, maxrss),
                "store_bytes": store, "store_disk_bytes": store_disk,
                "started_at": started, "pass": self.pass_, "candidate": self.candidate["sha256"],
                "cpu": pin, "alone": job.alone, "interference": interference, "disturbed": reasons,
                "sampler_error": sampler.error,
                "stdout": stdout, "stderr": self.scrub((tmp / "stderr").read_bytes().decode(errors="replace"), work, tmp)[-4000:],
                "files": files,
                "digests": json.loads(self.scrub(digests.read_text(), work, tmp)) if digests.exists() else None,
            }
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def kill_all(self):
        self.stopping.set()
        with self.lock:
            pids = list(self.running)
        for pid in pids:
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    def stop(self, job, rec, plain, diff, deep, why=None):
        lines = compare.explain(plain, rec, diff, deep) if diff else []
        summary = why or f"{job.sid} under {job.config} differs from plain Python in {len(diff)}: {diff[:8]}"
        write_json(self.pdir / "STOP.json", {"summary": summary, "sid": job.sid, "config": job.config,
                                             "candidate": self.candidate, "differences": diff, "explain": lines,
                                             "at": utcnow()})
        log("STOP:", summary, *("\n    " + x for x in lines))
        raise Stop(summary)

    # ------------------------------------------------------------ correctness

    def correctness(self, workers, budget_gib):
        self.record_machine()
        plain_jobs, light, alone = [], [], []
        for sid, folder, args in self.scripts:
            plain_jobs += [Job(sid, folder, args, c) for c in PLAIN]
            for c in self.configs:
                (alone if sid in ALONE else light).append(Job(sid, folder, args, c, alone=sid in ALONE))
        light.sort(key=lambda j: j.sid not in LONG)
        alone.sort(key=lambda j: j.sid != "s19")
        pending = plain_jobs + light + alone
        done = {}
        for job in list(pending):
            path = self.pdir / job.sid / f"{job.config}.json"
            if path.exists():
                done[(job.sid, job.config)] = json.loads(path.read_text())
                pending.remove(job)
        log(f"correctness of {self.candidate['wheel']} ({self.candidate['sha256'][:12]}): "
            f"{len(pending)} runs to go, {len(done)} recorded")
        judged = set()

        def judge(sid):
            p, c = done.get((sid, "python")), done.get((sid, "python-control"))
            if not (p and c):
                return
            for rec in (p, c):
                if rec["status"] != 0:
                    self.stop(Job(sid, "", "", rec["config"]), rec, rec, [], True,
                              why=f"plain Python fails on {sid} (status {rec['status']}): the environment is broken")
            ignore = compare.noise(p, c)
            for (s, config), rec in list(done.items()):
                if s != sid or config in PLAIN or (s, config) in judged:
                    continue
                judged.add((s, config))
                if rec["status"] in compare.UNFINISHED:
                    log(f"{s} {config}: not finished, memory ({rec['peak_rss'] / 2**30:.1f} GiB at the end)")
                    continue
                diff = compare.differences(p, rec, ignore)
                if diff:
                    self.stop(Job(s, "", "", config), rec, p, diff, True)

        for sid, _, _ in self.scripts:
            judge(sid)
        finished = queue.Queue()
        running = {}

        def worker(job):
            try:
                finished.put((job, self.run_one(job, deep=True)))
            except BaseException as exc:  # noqa: BLE001 (reported by the main thread)
                finished.put((job, exc))

        def fits(job):
            if job.config == "python-control" and (job.sid, "python") not in done:
                # after the first plain run, never beside it: run at the same moment, two runs
                # can read the same timer, and the control would miss that noise
                return False
            if not running:
                return True
            if job.alone or any(j.alone for j in running) or len(running) >= workers:
                return False
            return sum(j.peak for j in running) + job.peak <= budget_gib

        try:
            while pending or running:
                for job in list(pending):
                    if fits(job):
                        pending.remove(job)
                        running[job] = threading.Thread(target=worker, args=(job,), daemon=True)
                        running[job].start()
                    elif job.alone:
                        break  # what is alone waits for the pool to drain; nothing passes it
                job, rec = finished.get()
                running.pop(job)
                if isinstance(rec, BaseException):
                    raise rec
                if rec["status"] == "stopped":
                    continue
                log(f"{job.sid} {job.config}: {rec['status']} {rec['wall']:.1f}s peak {rec['peak_rss'] / 2**30:.1f} GiB"
                    + (" (alone)" if job.alone else ""))
                if rec["status"] in compare.UNFINISHED and not job.alone and job.config not in PLAIN:
                    write_json(self.pdir / job.sid / f"{job.config}.oom-shared.json", rec)
                    log(f"{job.sid} {job.config}: killed for memory beside other runs; again, alone")
                    retry = Job(job.sid, job.folder, job.args, job.config, alone=True)
                    pending.insert(next((i for i, j in enumerate(pending) if j.alone), len(pending)), retry)
                    continue
                write_json(self.pdir / job.sid / f"{job.config}.json", rec)
                done[(job.sid, job.config)] = rec
                judge(job.sid)
        except (Stop, KeyboardInterrupt):
            self.kill_all()
            for t in running.values():
                t.join()
            raise
        unfinished = sorted(f"{s} {c}" for (s, c), r in done.items() if r["status"] in compare.UNFINISHED)
        n = sum(1 for (_, c), r in done.items() if c not in PLAIN and r["status"] not in compare.UNFINISHED)
        write_json(self.pdir / "CLEAN.json", {
            "summary": f"clean: {n} runs under noWorkflow compute what plain Python computes"
                       + (f"; not finished for memory: {', '.join(unfinished)}" if unfinished else "")
                       + ("" if self.complete else " (a subset: --only or --configs)"),
            "complete": self.complete, "candidate": self.candidate, "unfinished": unfinished, "at": utcnow(),
            "estimate_s": {c: round(sum(r["wall"] for (_, cc), r in done.items() if cc == c)) for c in CONFIGS},
            # what one repetition of the timing pass would take, one run at a time: a rough
            # figure for the reservation (here the runs paid for the hook and shared the
            # machine; there they run without the turbo)
            "timing_repetition_h": round(sum(r["wall"] for (_, c), r in done.items()
                                             if c != "python-control" and r["status"] not in compare.UNFINISHED) / 3600, 1),
        })
        log("correctness: clean")

    # ------------------------------------------------------------ timing

    def timing(self, repetitions, retries, partial):
        base = self.results / "correctness"
        clean = base / "CLEAN.json"
        if not clean.exists():
            raise SystemExit("no clean correctness pass of this candidate in RESULTS: the timing pass comes after it")
        clean = json.loads(clean.read_text())
        if clean["candidate"]["sha256"] != self.candidate["sha256"]:
            raise SystemExit("the correctness pass in RESULTS is of another candidate")
        if not clean["complete"] and not partial:
            raise SystemExit("the correctness pass covered a subset; --partial only to try the harness")
        if not self.prep:
            log("WARNING: machine not prepared (prepare.py apply): the runs are not pinned, and nothing is measured "
                "about interference; these times are not the paper's")
            run_cpu = None
        else:
            run_cpu = self.prep["run_cpu"]
            os.sched_setaffinity(0, {self.prep["harness_cpu"]})
        self.record_machine()
        unfinished = set(clean["unfinished"])
        configs = ["python"] + self.configs
        log(f"timing of {self.candidate['wheel']} ({self.candidate['sha256'][:12]}): {repetitions} repetitions, "
            f"run CPU {run_cpu}" + (f"; not timed, out of memory in the correctness pass: {sorted(unfinished)}" if unfinished else ""))
        try:
            for rep in range(1, repetitions + 1):
                for sid, folder, args in self.scripts:
                    plain = json.loads((base / sid / "python.json").read_text())
                    ignore = compare.noise(plain, json.loads((base / sid / "python-control.json").read_text()), deep=False)
                    k = (rep - 1) % len(configs)
                    for config in configs[k:] + configs[:k]:
                        if f"{sid} {config}" in unfinished:
                            continue
                        job = Job(sid, folder, args, config)
                        path = self.pdir / sid / config / f"rep{rep:02d}.json"
                        if path.exists():
                            rec = json.loads(path.read_text())
                        else:
                            attempts = []
                            for attempt in range(1 + retries):
                                rec = self.run_one(job, deep=False, pin=run_cpu)
                                if rec["status"] == "stopped":
                                    raise KeyboardInterrupt
                                attempts.append({k2: rec[k2] for k2 in ("started_at", "status", "wall", "reported", "disturbed")})
                                if rec["status"] in compare.UNFINISHED or not rec["disturbed"] or attempt == retries:
                                    break
                                log(f"{sid} {config} rep {rep}: disturbed ({'; '.join(rec['disturbed'])}), again")
                            rec["repetition"], rec["attempts"] = rep, attempts
                            write_json(path, rec)
                            log(f"{sid} {config} rep {rep}: {rec['status']} {rec['wall']:.2f}s "
                                f"(reported {rec['reported']}) peak {rec['peak_rss'] / 2**30:.1f} GiB"
                                + (" STILL DISTURBED" if rec["disturbed"] else ""))
                        if rec["status"] in compare.UNFINISHED:
                            continue
                        diff = compare.differences(plain, rec, ignore, deep=False)
                        if diff:
                            self.stop(job, rec, plain, diff, False)
        except (Stop, KeyboardInterrupt):
            self.kill_all()
            raise
        write_json(self.pdir / "CLEAN.json", {
            "summary": f"clean: {repetitions} repetitions, every run computes what plain Python computes"
                       + ("" if self.complete else " (a subset: --only or --configs)"),
            "complete": self.complete, "candidate": self.candidate, "at": utcnow(),
        })
        log("timing: clean")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="pass_", required=True)
    for name in ("correctness", "timing"):
        p = sub.add_parser(name)
        p.add_argument("results")
        p.add_argument("--env", required=True)
        p.add_argument("--only", help="sids, comma-separated: try the harness on a subset")
        p.add_argument("--configs", help="configurations, comma-separated (plain Python always runs)")
        p.add_argument("--workdir", help="where each run gets its fresh copy (default: ENV/runs)")
        p.add_argument("--rss-cap", type=int, help="GiB: kill a run that holds more (a machine without the unit's cap)")
    c = sub.choices["correctness"]
    c.add_argument("--workers", type=int, default=6)
    c.add_argument("--budget", type=int, default=110, help="GiB the parallel runs may hold together (scripts.PEAK_GIB)")
    t = sub.choices["timing"]
    t.add_argument("--repetitions", type=int, default=10)
    t.add_argument("--retries", type=int, default=2, help="more runs of a disturbed repetition")
    t.add_argument("--partial", action="store_true", help="accept a correctness pass of a subset")
    a = ap.parse_args()
    gate = Gate(a, a.pass_)

    def terminate(signum, frame):
        gate.kill_all()
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, terminate)
    try:
        if a.pass_ == "correctness":
            gate.correctness(a.workers, a.budget)
        else:
            gate.timing(a.repetitions, a.retries, a.partial)
    except Stop:
        sys.exit(EXIT_DIFFERS)
    except KeyboardInterrupt:
        log("interrupted; the same command resumes")
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
