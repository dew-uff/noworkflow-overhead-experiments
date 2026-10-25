"""Loaded by every interpreter of the gate (PYTHONPATH), plain and under `now run`.

When MIRROR_OUT names a file, it seeds `random` and numpy's global generator
when the script's top level starts, so that two runs of an unseeded script
draw the same numbers. With MIRROR_MODE=full (the correctness pass) it also
records, for the code of the run directory (MIRROR_DIR):
- the return values of each function, as a count and a running digest per qualname, over
  its first MIRROR_RETURNS_CAP returns (100,000 by default), in the order of the calls:
  after that each of its return sites stops reporting the next time it is reached, so that
  a script of hundreds of millions of calls (s14, s20, s21) pays for a bounded number of
  callbacks, not one per call. The cap counts per function, not per return site: under
  `now run` the script is compiled from a rewritten tree, and its sites may differ;
- the final globals of __main__, one digest per name.
With MIRROR_MODE=seed (the timing pass) it only seeds, and then stops listening,
so that what the timing pass measures is the script and noWorkflow.
"""

import atexit
import hashlib
import json
import os
import pickle
import sys

_OUT = os.environ.get("MIRROR_OUT")
_FULL = os.environ.get("MIRROR_MODE", "full") == "full"
_DIR = os.path.realpath(os.environ.get("MIRROR_DIR", "/nonexistent")) + os.sep
_CAP = int(os.environ.get("MIRROR_RETURNS_CAP", "100000"))
_TOOL = 4


def _h(data):
    return hashlib.blake2b(data, digest_size=12).hexdigest()


def digest(v, depth=0):
    t = type(v)
    name = t.__module__ + "." + t.__qualname__
    if v is None or t in (bool, int, float, complex):
        return repr(v)
    if t in (str, bytes):
        return t.__name__ + ":" + (repr(v) if len(v) < 64 else _h(v.encode() if t is str else v))
    if depth > 6:
        return name + ":deep"
    if name == "numpy.ndarray":
        if v.dtype.hasobject:
            return "nd:" + _h("".join(digest(x, depth + 1) for x in v.ravel().tolist()).encode())
        import numpy as np

        return f"nd:{v.dtype}{v.shape}:" + _h(np.ascontiguousarray(v).tobytes())
    if t.__module__ == "numpy" or t.__module__.startswith("numpy."):
        return name + ":" + repr(v)
    if name in ("pandas.core.series.Series", "pandas.core.frame.DataFrame"):
        import pandas as pd

        return name + ":" + _h(pd.util.hash_pandas_object(v, index=True).values.tobytes() + repr(list(getattr(v, "columns", []))).encode())
    if t in (list, tuple):
        return t.__name__ + f"[{len(v)}]:" + _h("|".join(digest(x, depth + 1) for x in v).encode())
    if t is dict:
        return f"dict[{len(v)}]:" + _h("|".join(digest(k, depth + 1) + "=" + digest(x, depth + 1) for k, x in v.items()).encode())
    if t in (set, frozenset):
        return t.__name__ + f"[{len(v)}]:" + _h("|".join(sorted(digest(x, depth + 1) for x in v)).encode())
    if t.__module__.startswith(("matplotlib", "noworkflow")):
        return name
    try:
        return name + ":" + _h(pickle.dumps(v, protocol=4))
    except Exception:
        return name + ":unpicklable"


_returns = {}  # qualname -> [count, running digest]
_seeded = []


def _mine(code):
    name = code.co_filename  # "<string>", "<frozen ...>" are relative: never the script's
    return os.path.isabs(name) and os.path.realpath(name).startswith(_DIR)


def _on_start(code, offset):
    # only the script's top level matters, once: every code object reports a single start
    if code.co_name == "<module>" and not _seeded and _mine(code):
        _seeded.append(code.co_filename)
        import random

        random.seed(1234)
        try:
            import numpy

            numpy.random.seed(1234)
        except ImportError:
            pass
        if not _FULL:
            sys.monitoring.set_events(_TOOL, 0)
    return sys.monitoring.DISABLE


def _on_return(code, offset, value):
    if not _mine(code):
        return sys.monitoring.DISABLE
    entry = _returns.get(code.co_qualname)
    if entry is None:
        entry = _returns[code.co_qualname] = [0, hashlib.blake2b(digest_size=12)]
    if entry[0] >= _CAP:
        return sys.monitoring.DISABLE
    entry[0] += 1
    entry[1].update(digest(value).encode() + b"|")
    return None


def _dump():
    if _FULL:
        sys.monitoring.set_events(_TOOL, 0)
    if not _seeded:  # an interpreter that never ran the script (a child of `now`, say)
        return
    record = {"seeded": _seeded}
    if _FULL:
        main = sys.modules.get("__main__")
        glob = {}
        for k, v in list(vars(main).items()) if main else []:
            if k.startswith("__") or type(v).__name__ in ("module", "function", "type", "builtin_function_or_method"):
                continue
            try:
                glob[k] = digest(v)
            except Exception as exc:  # a digest must never change the outcome
                glob[k] = "error:" + type(exc).__name__
        record.update(returns={k: [n, h.hexdigest()] for k, (n, h) in _returns.items()}, globals=glob, returns_cap=_CAP)
    with open(_OUT, "w") as f:
        json.dump(record, f, indent=1, sort_keys=True)


if _OUT:
    sys.monitoring.use_tool_id(_TOOL, "mirror")
    sys.monitoring.register_callback(_TOOL, sys.monitoring.events.PY_START, _on_start)
    events = sys.monitoring.events.PY_START
    if _FULL:
        sys.monitoring.register_callback(_TOOL, sys.monitoring.events.PY_RETURN, _on_return)
        events |= sys.monitoring.events.PY_RETURN
    sys.monitoring.set_events(_TOOL, events)
    atexit.register(_dump)
