"""Compare each `now run` configuration with plain Python, per script.

usage: python compare.py OUTDIR [--verbose]
What two plain runs disagree on (python vs python-control) is nondeterministic and left out.
"""

import json
import pathlib
import re
import sys

TIME = re.compile(r"^-?\d+[.,]\d+(e-?\d+)?$")
ORDER = ["now", "d2", "d3", "cg", "cg-d2", "cg-d3", "e-none", "e-relevant"]


def facets(r):
    lines = r["stdout"].rstrip("\n").splitlines()
    if lines and TIME.match(lines[-1].strip()):
        lines[-1] = "<elapsed>"
    d = r["digests"] or {}
    f = {"status": str(r["status"]), "stdout": "\n".join(lines)}
    f.update({"file:" + k: v for k, v in r["files"].items()})
    f.update({"return:" + k: f"{n}x {h}" for k, (n, h) in (d.get("returns") or {}).items()})
    f.update({"global:" + k: v for k, v in (d.get("globals") or {}).items()})
    return f


def main():
    outdir = pathlib.Path(sys.argv[1])
    verbose = "--verbose" in sys.argv
    for sdir in sorted(outdir.iterdir(), key=lambda p: int(p.name[1:])):
        runs = {p.stem: json.loads(p.read_text()) for p in sdir.glob("*.json")}
        if "python" not in runs:
            continue
        base = facets(runs["python"])
        noise = set()
        if "python-control" in runs:
            ctl = facets(runs["python-control"])
            noise = {k for k in base.keys() | ctl.keys() if base.get(k) != ctl.get(k)}
        print(f"== {sdir.name}  plain: {runs['python']['elapsed']:.1f}s, {len(base)} facets, "
              f"nondeterministic: {sorted(noise) or 'none'}")
        for cfg in ORDER:
            if cfg not in runs:
                continue
            r = runs[cfg]
            fc = facets(r)
            diff = sorted(k for k in base.keys() | fc.keys() if k not in noise and base.get(k) != fc.get(k))
            verdict = "same" if not diff else f"DIFFERS in {len(diff)}: {diff[:8]}"
            print(f"  {cfg:11s} {str(r['status']):>7s} {r['elapsed']:8.1f}s store {r['store_bytes'] / 2**20:9.1f} MiB  {verdict}")
            if diff and verbose:
                for k in diff[:12]:
                    print(f"      {k}: plain={str(base.get(k))[:120]!r}\n      {' ' * len(k)}  now  ={str(fc.get(k))[:120]!r}")


if __name__ == "__main__":
    main()
