"""Prepare the measurement machine for the release gate, launch the gate in it, undo it.

  python3 prepare.py check                      what the machine has and what apply would do; changes nothing
  sudo python3 prepare.py apply [--run-cpu N --harness-cpu M --others LIST]
                                                the timing preparation: cores, SMT, frequency, services
  sudo python3 prepare.py launch PASS RESULTS [--memory-max 120G] -- python3 gate.py PASS RESULTS ...
                                                the gate as the calling user, in a unit with the memory cap
  sudo python3 prepare.py restore [--force]    undo apply, from the saved state; idempotent
  python3 prepare.py status

Linux with systemd and cgroup v2 only. The order on the machine: the reservation starts
(the lab's own tool, outside this repository), `apply` (timing pass only), `launch`,
the pass ends, `restore`, the reservation ends. Everything apply changes is runtime state
(sysfs, `systemctl --runtime`, stopped units): a reboot undoes it too, and the state file
lives in /run, which a reboot empties.
"""

import argparse
import datetime
import glob
import json
import os
import pathlib
import platform
import pwd
import shlex
import shutil
import subprocess
import sys

STATE_DIR = pathlib.Path("/run/nowgate")
STATE = STATE_DIR / "state.json"
SLICE = "nowgate.slice"
# The cap of the experiment (D28 of the paper's plan): what is left of the 128 GB, and the
# swap, stay with the operating system; a run of ours never swaps, where its time would
# stop meaning anything. The cap holds for the whole unit: the harness and its runs.
MEMORY_MAX = "120G"
# Background work that wakes up on its own, stopped while the timing pass runs: every active
# timer (apt's, fstrim, e2scrub, logrotate...) and the upgrades daemon. Stopping a timer only
# postpones it; restore starts again the ones that were active, and so does a reboot.
DAEMONS = ["unattended-upgrades.service"]
BUSY_UNITS = ["apt-daily.service", "apt-daily-upgrade.service"]
CONFINED = ["user.slice", "system.slice", "init.scope"]
CPU = pathlib.Path("/sys/devices/system/cpu")


def read(path, default=None):
    try:
        return pathlib.Path(path).read_text().strip()
    except OSError:
        return default


def write(path, value):
    pathlib.Path(path).write_text(str(value))


def cpulist(text):
    """'0-3,8,10-11' -> [0, 1, 2, 3, 8, 10, 11]"""
    out = []
    for part in (text or "").split(","):
        part = part.strip()
        if not part:
            continue
        a, _, b = part.partition("-")
        out.extend(range(int(a), int(b or a) + 1))
    return out


def cpustr(cpus):
    return ",".join(str(c) for c in sorted(cpus))


def run(*cmd, check=True):
    return subprocess.run(cmd, check=check, capture_output=True, text=True).stdout.strip()


def systemctl_show(unit, prop):
    return run("systemctl", "show", "-p", prop, "--value", unit, check=False)


# ---------------------------------------------------------------- what the machine has


def cores():
    """Physical cores as sorted lists of their CPUs (SMT siblings), each core once"""
    seen = {}
    for c in cpulist(read(CPU / "present")):
        sib = read(CPU / f"cpu{c}/topology/thread_siblings_list")
        key = tuple(cpulist(sib)) if sib else (c,)
        seen.setdefault(key, None)
    return sorted(seen, key=lambda k: k[0])


def hybrid():
    """(P CPUs, E CPUs) on an Intel hybrid processor, or None"""
    p, e = read("/sys/devices/cpu_core/cpus"), read("/sys/devices/cpu_atom/cpus")
    if p and e:
        return cpulist(p), cpulist(e)
    return None


def choose(run_cpu=None, harness_cpu=None, others=None):
    """The CPU of the runs, the CPU of the harness, the sibling to take offline, the CPUs of
    everything else. The runs and the harness go on the last two performance cores (never
    core 0, which takes interrupts that cannot move); everything else goes on the
    efficiency cores of a hybrid processor, or on the other cores."""
    all_cores = cores()
    h = hybrid()
    pcores = [k for k in all_cores if not h or k[0] in h[0]]
    if run_cpu is None or harness_cpu is None:
        if len(pcores) < 3:
            raise SystemExit(f"too few cores to set two aside: {all_cores}")
        run_core, harness_core = pcores[-1], pcores[-2]
        run_cpu = run_core[0] if run_cpu is None else run_cpu
        harness_cpu = harness_core[0] if harness_cpu is None else harness_cpu
    run_core = next(k for k in all_cores if run_cpu in k)
    harness_core = next(k for k in all_cores if harness_cpu in k)
    if run_core == harness_core:
        raise SystemExit("the runs and the harness must be on different physical cores")
    siblings = [c for c in run_core if c != run_cpu]
    if others is not None:
        rest = cpulist(others)
    elif h:
        rest = [c for c in h[1] if c not in run_core + harness_core]
    else:
        rest = [c for k in all_cores if k not in (run_core, harness_core) for c in k]
    if not rest:  # an empty AllowedCPUs= gives every CPU back: nothing would be confined
        raise SystemExit("no CPU left for the rest of the machine")
    if run_cpu in rest or any(c in rest for c in siblings):
        raise SystemExit("the rest of the machine cannot share the run's core")
    return {"run_cpu": run_cpu, "harness_cpu": harness_cpu, "offline": siblings, "others": rest,
            "run_core": list(run_core), "harness_core": list(harness_core)}


def turbo():
    """(path, value that means turbo is on, current value) of the turbo switch, or None"""
    if os.path.exists("/sys/devices/system/cpu/intel_pstate/no_turbo"):
        return "/sys/devices/system/cpu/intel_pstate/no_turbo", "0", read("/sys/devices/system/cpu/intel_pstate/no_turbo")
    if os.path.exists("/sys/devices/system/cpu/cpufreq/boost"):
        return "/sys/devices/system/cpu/cpufreq/boost", "1", read("/sys/devices/system/cpu/cpufreq/boost")
    return None


def governors():
    return {p.split("/")[5]: read(p) for p in sorted(glob.glob(str(CPU / "cpu[0-9]*/cpufreq/scaling_governor")))}


def os_release():
    for line in (read("/etc/os-release") or "").splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip('"')
    return None


def cpu_model():
    for line in (read("/proc/cpuinfo") or "").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor() or None


def meminfo(key):
    for line in (read("/proc/meminfo") or "").splitlines():
        if line.startswith(key + ":"):
            return int(line.split()[1]) * 1024
    return None


def describe():
    """The machine as the results record it; needs no root and changes nothing. No host
    name and no user name: the results are public."""
    d = {
        "os": os_release() or platform.platform(),
        "kernel": platform.release(),
        "cpu": cpu_model(),
        "cpus": os.cpu_count(),
        "memory_bytes": meminfo("MemTotal"),
        "swap_bytes": meminfo("SwapTotal"),
    }
    if sys.platform != "linux":
        return d
    h = hybrid()
    t = turbo()
    d.update({
        "cores": [list(k) for k in cores()],
        "performance_cpus": h[0] if h else None,
        "efficiency_cpus": h[1] if h else None,
        "online": read(CPU / "online"),
        "cpufreq_driver": read(CPU / "cpu0/cpufreq/scaling_driver"),
        "turbo": None if not t else (t[2] == t[1]),
        "governors": sorted(set(governors().values())),
        "max_freq_khz": {c: read(CPU / f"cpu{c}/cpufreq/cpuinfo_max_freq") for c in (0, (os.cpu_count() or 1) - 1)},
        "cgroup_controllers": read("/sys/fs/cgroup/cgroup.controllers"),
        "systemd": run("systemctl", "--version", check=False).split("\n")[0],
        "systemd_oomd": run("systemctl", "is-active", "systemd-oomd.service", check=False),
        "units": {u: run("systemctl", "is-active", u, check=False) for u in units()},
        "confined_cpus": {u: effective(u) for u in CONFINED},
    })
    return d


def units():
    """The units apply stops: the active timers and DAEMONS"""
    timers = run("systemctl", "list-units", "--type=timer", "--state=active", "--plain", "--no-legend", check=False)
    return [line.split()[0] for line in timers.splitlines() if line.strip()] + DAEMONS


def effective(unit):
    """The CPUs a unit's cgroup may use now, as the kernel sees them"""
    cg = systemctl_show(unit, "ControlGroup")
    return read(f"/sys/fs/cgroup{cg}/cpuset.cpus.effective") if cg else None


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else None


# ---------------------------------------------------------------- commands


def cmd_check(a):
    d = describe()
    print(json.dumps(d, indent=1))
    if sys.platform != "linux":
        print("\nnot Linux: apply, launch and restore do nothing here")
        return
    print("\nswap:", run("swapon", "--show", check=False) or "none")
    print("\ntimers (apply stops the active ones):")
    print(run("systemctl", "list-timers", "--no-pager", check=False))
    try:
        c = choose(a.run_cpu, a.harness_cpu, a.others)
        print("\napply would: runs on CPU", c["run_cpu"], "with", c["offline"] or "no sibling", "offline;",
              "the harness on CPU", c["harness_cpu"], "; user.slice, system.slice and init.scope on", cpustr(c["others"]),
              ";", "turbo off," if turbo() else "no turbo switch;", "governor performance" if governors() else "no cpufreq;",
              "stop", ", ".join(u for u in units() if run("systemctl", "is-active", u, check=False) == "active"))
    except SystemExit as exc:
        print("\napply would refuse:", exc)
    if "cpuset" not in (d["cgroup_controllers"] or ""):
        print("\nWARNING: no cpuset controller in cgroup v2: AllowedCPUs= would do nothing")
    if shutil.which("bench"):
        print("\nbench status:", run("bench", "status", check=False))
    s = state()
    print("\nprepared now:", "yes, since " + s["applied_at"] if s else "no")


def need_root():
    if os.geteuid() != 0:
        raise SystemExit("needs root: sudo python3 prepare.py ...")
    if sys.platform != "linux":
        raise SystemExit("Linux only")


def cmd_apply(a):
    need_root()
    if STATE.exists():
        raise SystemExit(f"already prepared ({STATE}); restore first")
    busy = [u for u in BUSY_UNITS if run("systemctl", "is-active", u, check=False) == "active"]
    if busy:
        raise SystemExit(f"{', '.join(busy)} running now: wait for it to end")
    if shutil.which("bench") and subprocess.run(["bench", "status"], capture_output=True).returncode != 0:
        print("WARNING: `bench status` does not report a reservation", file=sys.stderr)
    c = choose(a.run_cpu, a.harness_cpu, a.others)
    t = turbo()
    s = dict(c)
    s.update({
        "applied_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "turbo": {"path": t[0], "on": t[1], "before": t[2]} if t else None,
        "governors": governors(),
        "allowed_cpus": {u: systemctl_show(u, "AllowedCPUs") for u in CONFINED},
        "effective_cpus": {u: effective(u) for u in CONFINED},
        "units": {u: run("systemctl", "is-active", u, check=False) for u in units()},
        "done": [],
    })
    STATE_DIR.mkdir(exist_ok=True)

    def save():
        STATE.write_text(json.dumps(s, indent=1))
        STATE.chmod(0o644)

    save()  # before the first change: restore undoes whatever a failure leaves half done
    for u in s["units"]:
        if s["units"][u] == "active":
            run("systemctl", "stop", u)
    s["done"].append("units")
    save()
    for u in CONFINED:
        run("systemctl", "set-property", "--runtime", u, "AllowedCPUs=" + cpustr(c["others"]))
    s["done"].append("allowed_cpus")
    save()
    for cpu in c["offline"]:
        write(CPU / f"cpu{cpu}/online", 0)
    s["done"].append("offline")
    save()
    if t:
        write(t[0], "1" if t[1] == "0" else "0")
    for name in governors():  # the online CPUs: the sibling just left
        write(CPU / f"{name}/cpufreq/scaling_governor", "performance")
    s["done"].append("frequency")
    save()
    print(json.dumps({k: s[k] for k in ("run_cpu", "harness_cpu", "offline", "others")}))
    print(f"prepared; state in {STATE}. Undo with `sudo python3 {sys.argv[0]} restore` before the reservation ends.")


def cmd_restore(a):
    need_root()
    s = state()
    if not s:
        print("nothing to restore")
        return
    active = [u for u in run("systemctl", "list-units", "--plain", "--no-legend", "nowgate-*", check=False).splitlines() if " running " in u]
    if active and not a.force:
        raise SystemExit(f"a pass is still running ({active[0].split()[0]}): stop it first, or --force")
    errors = []

    def attempt(what, fn):
        try:
            fn()
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"{what}: {exc}")

    # Every step, whatever apply got to: each one only puts back a value saved before
    # apply changed anything, which is harmless where apply never got.
    for cpu in s["offline"]:  # first: an offline CPU has no governor to restore
        attempt(f"cpu{cpu} online", lambda cpu=cpu: write(CPU / f"cpu{cpu}/online", 1))
    for name, gov in s["governors"].items():
        attempt(f"governor of {name}", lambda name=name, gov=gov: write(CPU / f"{name}/cpufreq/scaling_governor", gov))
    if s["turbo"]:
        attempt("turbo", lambda: write(s["turbo"]["path"], s["turbo"]["before"]))
    for u, before in s["allowed_cpus"].items():
        if not before:
            # an empty AllowedCPUs= changes systemd's view only: the cgroup keeps the CPUs
            # apply gave it. Every CPU first, then empty, as it was.
            attempt(f"AllowedCPUs of {u}", lambda u=u: run("systemctl", "set-property", "--runtime", u, "AllowedCPUs=" + read(CPU / "present")))
        attempt(f"AllowedCPUs of {u}", lambda u=u, before=before: run("systemctl", "set-property", "--runtime", u, "AllowedCPUs=" + before))
    for u, before in s["effective_cpus"].items():
        if effective(u) != before:
            errors.append(f"{u} may use CPUs {effective(u)}, not {before} as before apply")
    for u, before in s["units"].items():
        if before == "active":
            attempt(f"start {u}", lambda u=u: run("systemctl", "start", u))
    if errors:
        raise SystemExit("restore incomplete, state kept:\n" + "\n".join(errors))
    STATE.unlink()
    print("restored")


def cmd_launch(a):
    need_root()
    uid, gid = int(os.environ.get("SUDO_UID", -1)), int(os.environ.get("SUDO_GID", -1))
    if uid < 0:
        raise SystemExit("run it through sudo, so that the gate runs as you")
    user = pwd.getpwuid(uid)
    cmd = a.cmd
    if not cmd:
        raise SystemExit("nothing to launch: prepare.py launch PASS RESULTS -- python3 gate.py ...")
    s = state()
    if a.pass_ == "timing" and not s:
        raise SystemExit("the timing pass runs on a prepared machine: apply first")
    results = pathlib.Path(a.results).resolve()
    results.mkdir(parents=True, exist_ok=True)
    os.chown(results, uid, gid)
    log = results / f"{a.pass_}.log"
    log.touch()
    os.chown(log, uid, gid)
    unit = f"nowgate-{a.pass_}"
    props = [f"MemoryMax={a.memory_max}", "MemorySwapMax=0", "OOMPolicy=continue", "ManagedOOMPreference=avoid",
             f"StandardOutput=append:{log}", f"StandardError=append:{log}"]
    if a.pass_ == "timing":
        props.append("AllowedCPUs=" + cpustr([s["run_cpu"], s["harness_cpu"]]))
    env = {"HOME": user.pw_dir, "USER": user.pw_name, "LOGNAME": user.pw_name,
           "PATH": os.environ.get("SUDO_PATH") or f"{user.pw_dir}/.local/bin:/usr/local/bin:/usr/bin:/bin",
           "LANG": os.environ.get("LANG", "C.UTF-8")}
    argv = ["systemd-run", f"--unit={unit}", f"--slice={SLICE}", f"--uid={uid}", f"--gid={gid}",
            f"--working-directory={os.getcwd()}", "--collect"]
    argv += [f"--property={p}" for p in props] + [f"--setenv={k}={v}" for k, v in env.items()] + ["--"] + cmd
    print(shlex.join(argv))
    subprocess.run(argv, check=True)
    print(f"running as {unit}: `tail -f {log}`, `systemctl status {unit}`; it ends by itself.")


def cmd_status(a):
    s = state()
    print(json.dumps(s, indent=1) if s else "not prepared")
    if sys.platform == "linux":
        print(run("systemctl", "list-units", "--plain", "--no-legend", "nowgate-*", check=False) or "no pass running")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("check", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--run-cpu", type=int)
        p.add_argument("--harness-cpu", type=int)
        p.add_argument("--others", help="CPU list for everything else (default: the efficiency cores, or the other cores)")
    sub.add_parser("restore").add_argument("--force", action="store_true")
    sub.add_parser("status")
    p = sub.add_parser("launch")
    p.add_argument("pass_", choices=["correctness", "timing"], metavar="PASS")
    p.add_argument("results")
    p.add_argument("--memory-max", default=MEMORY_MAX, help="the cap of the unit (a lower one only to try the harness)")
    argv = sys.argv[1:]
    cmd = argv[argv.index("--") + 1:] if "--" in argv else []
    a = ap.parse_args(argv[:len(argv) - len(cmd) - (1 if cmd or "--" in argv else 0)])
    a.cmd = cmd
    {"check": cmd_check, "apply": cmd_apply, "restore": cmd_restore, "launch": cmd_launch, "status": cmd_status}[a.command](a)


if __name__ == "__main__":
    main()
