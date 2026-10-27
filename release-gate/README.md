# Release gate: the evaluation runs the release candidate

From 2.2.0 on, the paper's evaluation is also a gate of the release
([gems-uff/noworkflow#469](https://github.com/gems-uff/noworkflow/issues/469)): the wheel that
step 4 of noWorkflow's `release` skill builds and inspects runs the 21 scripts of this
repository with plain Python and under the eight configurations of the paper, and **a run that
computes something other than plain Python stops the release**. Only a wheel that passes is
tagged and uploaded, and the paper's numbers are this wheel's. `measurement-2.1.3/` holds the
measurement of 2.1.3 that led here.

| File | What it does |
|---|---|
| `scripts.py` | The 21 scripts with the arguments of `../run.sh`, the configurations, which scripts run alone |
| `requirements.txt` | What the scripts import, pinned (`requirements.in`, resolved for Linux and Python 3.12) |
| `setup.py` | The candidate's environment: the scripts ready to run, a venv with the wheel, `env.json` |
| `gate.py` | The two passes, correctness and timing; one JSON per run |
| `hook/sitecustomize.py` | Loaded into every run: seeds, and records what the script's functions returned |
| `compare.py` | The verdicts and the times, per script and configuration |
| `prepare.py` | The measurement machine: checks it, prepares it for timing, launches a pass, undoes it all |

## Running the gate

On Linux with systemd and cgroup v2, Python 3.12 or later (the hook uses `sys.monitoring`),
`uv` on the `PATH` (or `python3 -m venv` and pip), a checkout of this repository, and the
wheel of step 4 with its sha256. `W` is that wheel, `V` its version, `H` the first 12 digits
of its sha256.

**1. The candidate's environment** (minutes; fetches the HDF5 file of s5 from Git LFS when the
checkout holds only its pointer):

```bash
cd release-gate
python3 setup.py $W ~/gate/env-$V-$H --python python3.12
```

**2. The machine is reserved** with the lab's own tool ([`lock`](https://github.com/gems-uff/lock)), outside this repository: no other
users while either pass runs.

**3. The correctness pass**, in parallel. `prepare.py launch` runs the gate as the calling user
in a systemd unit capped at 120 GiB of memory without swap, so that what a run cannot fit is a
result and the rest of the machine stays up:

```bash
R=results/$V-$H
sudo python3 prepare.py launch correctness $R -- ~/gate/env-$V-$H/venv/bin/python gate.py correctness $R --env ~/gate/env-$V-$H
tail -f $R/correctness.log
```

It ends by itself, with `$R/correctness/CLEAN.json` (exit 0) or `STOP.json` (exit 1), which
names the script, the configuration and each value that differs, on both sides
(`python3 compare.py $R --verbose` shows them all). **On a stop**, nothing is tagged: the
defect gets its issue, the fix is integrated as any other, and the release restarts from the
bump with a new wheel, which is a new candidate in a new results directory. On a clean pass,
`CLEAN.json` says how long one repetition of the timing pass would take
(`timing_repetition_h`), for the reservation of the timing pass.

The same command resumes an interrupted pass (`sudo systemctl stop nowgate-correctness`,
a reboot): a run already recorded is not run again, and a results directory refuses another
candidate.

**4. The timing pass**, one run at a time, after a clean correctness pass of the same candidate:

```bash
python3 prepare.py check                 # what the machine has, and what apply would do
sudo python3 prepare.py apply            # after the reservation starts
sudo python3 prepare.py launch timing $R -- ~/gate/env-$V-$H/venv/bin/python gate.py timing $R --env ~/gate/env-$V-$H
tail -f $R/timing.log
sudo python3 prepare.py restore          # when it ends, before the reservation does
```

**5. The results**: `python3 compare.py $R`, and `$R` committed here, run records and machine
records included (they hold no user or host name).

## What is compared

A run starts from a fresh copy of the script's folder and is compared with plain Python on its
status, its stdout (the elapsed time the script prints last is masked), the SHA-1 of every
file it leaves (the store excluded) and, in the correctness pass, the digests of what each
function of the script returned and of the script's final globals. Plain Python runs twice in
the correctness pass, one run after the other, and whatever the two disagree on (timers,
`__pycache__`) is left out of every comparison. The hook seeds `random` and numpy at the start
of the script, under plain Python and under noWorkflow alike.

**A run that does not finish** because the memory cap killed it is recorded as `oom`, with
the memory it reached, and is not repeated: it computed nothing to compare, and it is a result
of the evaluation. Killed while other runs shared the cap, it runs again alone first.

## What shapes the numbers

These choices are recorded with every result (`machine-*.json` of each pass, the fields of
each run) and the paper's methodology states them.

- **No time limit.** The paper's evaluation stopped every run at 30 minutes, and s14, s20 and
  s21 never finished under noWorkflow; here they run with the original input until they end,
  or until the memory cap ends them.
- **Two times per run**: `reported`, what the script prints on its last line (a
  `perf_counter` around its own body, which is what the paper's evaluation reported), and
  `wall`, the whole process, noWorkflow's start and the writing of the store included. Also
  `user` and `sys` CPU time, the peak resident memory, and the store's size in bytes and on
  disk.
- **The timing pass on a prepared machine** (`prepare.py apply`): its runs pinned to one CPU of
  a performance core whose SMT sibling is offline, the gate on a CPU of another performance
  core, everything else (the `user.slice`, `system.slice` and `init.scope` cgroups) on the
  efficiency cores; turbo off and the `performance` governor; every active systemd timer and
  `unattended-upgrades` stopped. `restore` puts each of these back as `apply` found it, and
  fails, keeping its state, when the CPUs of a cgroup are not those it had.
- **One thread** for the numerical libraries (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and
  the like), in both passes.
- **The order of the configurations rotates** in each repetition of the timing pass (10 by
  default, as in the paper), plain Python included.
- **A rest before each repetition** (`--rest 600`, off by default): a repetition writes and
  deletes hundreds of GiB of stores, and the start of the next one, with noWorkflow writing a
  new store per run, was measured a few hundredths of a second slower on the SSD. The gate
  waits that long before the first run of each repetition that still has runs, and each run
  records the rest it came after (`rest_s`), so that runs made before and after the option
  was turned on can be told apart.
- **Interference** is sampled every second during a timing run: other work on the run's CPU
  (its busy time beyond the run's own CPU time), the CPUs busy elsewhere, the run CPU's
  frequency against its maximum, thermal throttling, and the processes that used the CPU
  (`root:`, `self:` or `other:` and the command). A run counts as disturbed past the
  thresholds of `gate.DISTURBED` and is run again, up to twice more; each attempt is kept.
- **The hook weighs on the correctness pass only.** There it records the first 100,000
  returns of each function and then stops listening, which bounds its cost on scripts of
  hundreds of millions of calls; in the timing pass it only seeds and then switches off, so
  the timing runs are compared on status, stdout and files.
- **Memory in the correctness pass**: the runs share a budget of 110 GiB by the peaks of
  `scripts.PEAK_GIB`, and s14, s19, s20 and s21 run under noWorkflow with nothing beside them.

## Trying it without the machine

`--only s4,s6` and `--configs now,d2` run a subset (`CLEAN.json` then says `"complete":
false`, and the timing pass needs `--partial` to follow it); `--rss-cap GiB` kills a run that
holds more, where no unit caps the memory; `prepare.py launch --memory-max 600M` lowers the
cap to make a run hit it; `prepare.py apply --run-cpu N --harness-cpu M --others LIST` for a
machine where the defaults do not fit. Off Linux, the passes run unpinned and without the
interference samples, and `prepare.py` does nothing but `check`.
