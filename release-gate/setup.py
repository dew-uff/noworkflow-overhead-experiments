"""Make the environment of one candidate: the scripts, ready to run, and a venv with the wheel.

usage: python3 setup.py WHEEL ENV [--python python3.12]

ENV gets:
- src/: a copy of the 21 scripts' folders of this repository, with the SQLite file of s2
  unzipped and the HDF5 file of s5 fetched from Git LFS (its sha256 checked against the
  pointer) when the checkout holds only the pointer;
- the wheel itself, and venv/ with it and requirements.txt installed (uv when it is on the
  PATH, otherwise venv and pip);
- env.json: the wheel's name and sha256, the version `now --version` prints, the Python,
  what the venv holds (`pip freeze`), this repository's commit.
gate.py refuses an ENV whose wheel no longer has the recorded sha256.
"""

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from scripts import SCRIPTS  # noqa: E402

LFS_MEDIA = "https://media.githubusercontent.com/media/dew-uff/noworkflow-overhead-experiments/{commit}/{path}"
S2_ZIP = "03dataoneexps/03dataoneexps_exp03_46_A_Method_For_Calculating/cee6440_ex3_loganriver.zip"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True, text=True).stdout.strip()


def lfs_pointer(path):
    """(oid, size) when path holds a Git LFS pointer instead of the file"""
    if path.stat().st_size > 1024:
        return None
    text = path.read_text(errors="replace")
    if not text.startswith("version https://git-lfs.github.com/spec/"):
        return None
    fields = dict(line.split(" ", 1) for line in text.splitlines() if " " in line)
    return fields["oid"].removeprefix("sha256:"), int(fields["size"])


def copy_sources(src, commit):
    if src.exists():
        shutil.rmtree(src)
    for _, folder, _ in SCRIPTS:
        shutil.copytree(REPO / folder, src / folder, symlinks=True)
    with zipfile.ZipFile(src / S2_ZIP) as z:
        z.extractall((src / S2_ZIP).parent)
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        pointer = lfs_pointer(path)
        if not pointer:
            continue
        rel = path.relative_to(src).as_posix()
        url = LFS_MEDIA.format(commit=commit, path=rel)
        print(f"fetching {rel} from Git LFS", flush=True)
        tmp = path.with_suffix(path.suffix + ".part")
        with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:  # noqa: S310 (a fixed https URL)
            shutil.copyfileobj(r, f)
        if (sha256(tmp), tmp.stat().st_size) != pointer:
            tmp.unlink()
            raise SystemExit(f"{rel}: what Git LFS served does not match the pointer")
        tmp.replace(path)


def make_venv(env, wheel, python):
    venv = env / "venv"
    if venv.exists():
        shutil.rmtree(venv)
    reqs = HERE / "requirements.txt"
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", "--no-python-downloads", "--python", python, str(venv)], check=True)
        subprocess.run(["uv", "pip", "install", "--python", str(venv / "bin" / "python"), "-r", str(reqs), str(wheel)], check=True)
        freeze = ["uv", "pip", "freeze", "--python", str(venv / "bin" / "python")]
    else:
        subprocess.run([python, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(venv / "bin" / "python"), "-m", "pip", "install", "-r", str(reqs), str(wheel)], check=True)
        freeze = [str(venv / "bin" / "python"), "-m", "pip", "freeze"]
    return subprocess.run(freeze, check=True, capture_output=True, text=True).stdout.splitlines()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wheel")
    ap.add_argument("env")
    ap.add_argument("--python", default="python3.12")
    a = ap.parse_args()
    env = pathlib.Path(a.env).resolve()
    env.mkdir(parents=True, exist_ok=True)
    wheel = env / pathlib.Path(a.wheel).name
    if pathlib.Path(a.wheel).resolve() != wheel:
        shutil.copy2(a.wheel, wheel)
    commit = git("rev-parse", "HEAD")
    copy_sources(env / "src", commit)
    freeze = make_venv(env, wheel, a.python)
    bin_ = env / "venv" / "bin"
    version = subprocess.run([str(bin_ / "now"), "--version"], check=True, capture_output=True, text=True)
    python = subprocess.run([str(bin_ / "python"), "-c", "import sys; print(sys.version.split()[0])"],
                            check=True, capture_output=True, text=True).stdout.strip()
    record = {
        "wheel": wheel.name,
        "sha256": sha256(wheel),
        "version": (version.stdout + version.stderr).strip(),
        "python": python,
        "freeze": freeze,
        "scripts_commit": commit,
        "scripts_dirty": bool(git("status", "--porcelain", "--", *{f.split("/")[0] for _, f, _ in SCRIPTS})),
    }
    (env / "env.json").write_text(json.dumps(record, indent=1))
    print(json.dumps({k: record[k] for k in ("wheel", "sha256", "version", "python", "scripts_commit", "scripts_dirty")}, indent=1))


if __name__ == "__main__":
    main()
