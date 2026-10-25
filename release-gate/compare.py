"""Compare each `now run` configuration with plain Python, per script.

usage: python3 compare.py RESULTS [--verbose]

RESULTS is a directory gate.py wrote: its correctness pass (correctness/<sid>/<config>.json)
and, when it ran, its timing pass (timing/<sid>/<config>/rep<NN>.json). What the two plain
runs of the correctness pass disagree on (python against python-control) is
nondeterministic and left out of every comparison.
"""

import json
import pathlib
import re
import statistics
import sys

TIME = re.compile(r"^-?\d+[.,]\d+(e-?\d+)?$")
ORDER = ["now", "d2", "d3", "cg", "cg-d2", "cg-d3", "e-none", "e-relevant"]
# A run that did not finish because of the memory cap is a result (D28 of the paper's plan),
# not something to compare: it computed nothing.
UNFINISHED = ("oom", "memory-cap")


def reported(stdout):
    """The elapsed time the script prints on its last line (the paper's measure), or None"""
    lines = stdout.rstrip("\n").splitlines()
    if lines and TIME.match(lines[-1].strip()):
        return float(lines[-1].strip().replace(",", "."))
    return None


def facets(r, deep=True):
    """What a run computed. deep adds the digests of returns and globals (correctness pass)."""
    lines = r["stdout"].rstrip("\n").splitlines()
    if lines and TIME.match(lines[-1].strip()):
        lines[-1] = "<elapsed>"
    f = {"status": str(r["status"]), "stdout": "\n".join(lines)}
    f.update({"file:" + k: v for k, v in r["files"].items()})
    if deep:
        d = r["digests"] or {}
        f.update({"return:" + k: f"{n}x {h}" for k, (n, h) in (d.get("returns") or {}).items()})
        f.update({"global:" + k: v for k, v in (d.get("globals") or {}).items()})
    return f


def noise(plain, control, deep=True):
    """The facets two plain runs disagree on"""
    a, b = facets(plain, deep), facets(control, deep)
    return {k for k in a.keys() | b.keys() if a.get(k) != b.get(k)}


def differences(plain, run, ignore, deep=True):
    """The facets where run differs from plain, minus ignore; [] when it computed the same"""
    a, b = facets(plain, deep), facets(run, deep)
    return sorted(k for k in a.keys() | b.keys() if k not in ignore and a.get(k) != b.get(k))


def explain(plain, run, diff, deep=True, limit=12):
    """Lines that show each differing facet on both sides"""
    a, b = facets(plain, deep), facets(run, deep)
    out = []
    for k in diff[:limit]:
        out.append(f"{k}: plain={str(a.get(k))[:160]!r}")
        out.append(f"{' ' * len(k)}  now  ={str(b.get(k))[:160]!r}")
    return out


def _load(sdir):
    return {p.stem: json.loads(p.read_text()) for p in sdir.glob("*.json")}


def _sid_order(p):
    return int(p.name[1:]) if p.name[1:].isdigit() else 0


def report_correctness(cdir, verbose):
    for sdir in sorted((p for p in cdir.iterdir() if p.is_dir()), key=_sid_order):
        runs = _load(sdir)
        if "python" not in runs:
            continue
        ignore = noise(runs["python"], runs["python-control"]) if "python-control" in runs else set()
        print(f"== {sdir.name}  plain: {runs['python']['wall']:.1f}s, peak {runs['python']['peak_rss'] / 2**30:.1f} GiB, "
              f"nondeterministic: {sorted(ignore) or 'none'}")
        for cfg in ORDER:
            if cfg not in runs:
                continue
            r = runs[cfg]
            if r["status"] in UNFINISHED:
                verdict = "not finished: memory"
            else:
                diff = differences(runs["python"], r, ignore)
                verdict = "same" if not diff else f"DIFFERS in {len(diff)}: {diff[:8]}"
                if diff and verbose:
                    verdict += "\n      " + "\n      ".join(explain(runs["python"], r, diff))
            print(f"  {cfg:11s} {str(r['status']):>7s} {r['wall']:9.1f}s peak {r['peak_rss'] / 2**30:6.1f} GiB "
                  f"store {r['store_bytes'] / 2**20:9.1f} MiB  {verdict}")


def report_timing(tdir):
    print("\n== timing (median over the accepted repetitions; wall = the process, reported = the script's own line)")
    for sdir in sorted((p for p in tdir.iterdir() if p.is_dir()), key=_sid_order):
        print(f"== {sdir.name}")
        for cfg in ["python"] + ORDER:
            reps = [json.loads(p.read_text()) for p in sorted((sdir / cfg).glob("rep*.json"))] if (sdir / cfg).is_dir() else []
            if not reps:
                continue
            done = [r for r in reps if r["status"] not in UNFINISHED]
            walls = [r["wall"] for r in done]
            reps_reported = [r["reported"] for r in done if r["reported"] is not None]
            disturbed = sum(1 for r in reps if r.get("disturbed"))
            line = f"  {cfg:11s} n={len(reps):2d}"
            if walls:
                line += f" wall {statistics.median(walls):9.2f}s"
            if reps_reported:
                line += f" reported {statistics.median(reps_reported):9.2f}s"
            line += f" peak {max(r['peak_rss'] for r in reps) / 2**30:6.1f} GiB"
            if len(done) < len(reps):
                line += f"  {len(reps) - len(done)} not finished: memory"
            if disturbed:
                line += f"  {disturbed} still disturbed after the retries"
            print(line)


def main():
    root = pathlib.Path(sys.argv[1])
    verbose = "--verbose" in sys.argv
    for name in ("STOP.json", "CLEAN.json"):
        for p in sorted(root.glob(f"*/{name}")):
            print(f"{p.relative_to(root)}: {json.loads(p.read_text())['summary']}")
    if (root / "correctness").is_dir():
        report_correctness(root / "correctness", verbose)
    if (root / "timing").is_dir():
        report_timing(root / "timing")


if __name__ == "__main__":
    main()
