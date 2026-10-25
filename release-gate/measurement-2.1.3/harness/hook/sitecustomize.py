"""Loaded by every interpreter of the measurement (PYTHONPATH), plain and under `now run`.

When MIRROR_OUT names a file, it records, for the code of the run directory (MIRROR_DIR):
- the return values of each function, as a call count and a rolling digest per qualname;
- the final globals of __main__, one digest per name;
and seeds `random` and numpy's global generator when the script's top level starts,
so that two runs of an unseeded script draw the same numbers.
"""

import atexit
import hashlib
import json
import os
import pickle
import sys

_OUT = os.environ.get("MIRROR_OUT")
_DIR = os.path.realpath(os.environ.get("MIRROR_DIR", "/nonexistent")) + os.sep
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


_returns = {}
_seeded = []


def _mine(code):
    name = code.co_filename  # "<string>", "<frozen ...>" are relative: never the script's
    return os.path.isabs(name) and os.path.realpath(name).startswith(_DIR)


def _on_start(code, offset):
    if not _mine(code):
        return sys.monitoring.DISABLE
    if code.co_name == "<module>" and not _seeded:
        _seeded.append(code.co_filename)
        import random

        random.seed(1234)
        try:
            import numpy

            numpy.random.seed(1234)
        except ImportError:
            pass
    return None


def _on_return(code, offset, value):
    if not _mine(code):
        return sys.monitoring.DISABLE
    key = code.co_qualname
    count, acc = _returns.get(key, (0, ""))
    _returns[key] = (count + 1, _h((acc + digest(value)).encode()))
    return None


def _dump():
    sys.monitoring.set_events(_TOOL, 0)
    if not _seeded:  # an interpreter that never ran the script (a child of `now`, say)
        return
    main = sys.modules.get("__main__")
    glob = {}
    for k, v in list(vars(main).items()) if main else []:
        if k.startswith("__") or type(v).__name__ in ("module", "function", "type", "builtin_function_or_method"):
            continue
        try:
            glob[k] = digest(v)
        except Exception as exc:  # a digest must never change the outcome
            glob[k] = "error:" + type(exc).__name__
    with open(_OUT, "w") as f:
        json.dump({"seeded": _seeded, "returns": _returns, "globals": glob}, f, indent=1, sort_keys=True)


if _OUT:
    sys.monitoring.use_tool_id(_TOOL, "mirror")
    sys.monitoring.register_callback(_TOOL, sys.monitoring.events.PY_START, _on_start)
    sys.monitoring.register_callback(_TOOL, sys.monitoring.events.PY_RETURN, _on_return)
    sys.monitoring.set_events(_TOOL, sys.monitoring.events.PY_START | sys.monitoring.events.PY_RETURN)
    atexit.register(_dump)
