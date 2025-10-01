#!/usr/bin/env python3
"""
Test CLI compatible with: python -m test -m <malware_path> -b <benign_path>

Accepts folders or archives (zip, tar, tar.gz, tgz, tar.bz2).
When archives are provided, they are extracted to a temporary directory.
Sends files to the running Docker/local service at http://localhost:8080/ via
POST / with Content-Type: application/octet-stream and reports simple accuracy.
"""
import os
import sys
import argparse
import shutil
import tempfile
import requests
from pathlib import Path
from typing import Iterable, List, Tuple


SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8080/")
TIMEOUT = 30


def _is_archive(path: Path) -> bool:
    lower = path.name.lower()
    return lower.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2"))


def _extract_if_archive(src: Path) -> Path:
    if not _is_archive(src):
        return src
    tmpdir = Path(tempfile.mkdtemp(prefix="ds_mal_"))
    shutil.unpack_archive(str(src), extract_dir=str(tmpdir))
    return tmpdir


def _iter_executables(root: Path) -> Iterable[Path]:
    exts = {".exe", ".dll", ".sys", ".scr"}
    if root.is_dir():
        for p in root.rglob("*"):
            if p.is_file() and (p.suffix.lower() in exts or p.suffix == ""):
                yield p
    elif root.is_file():
        yield root


def _score_file(path: Path) -> Tuple[bool, str]:
    try:
        with open(path, "rb") as f:
            data = f.read()
        resp = requests.post(
            SERVER_URL,
            data=data,
            headers={"Content-Type": "application/octet-stream"},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            js = resp.json()
            return True, str(js.get("result", "unknown"))
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


def _eval_folder(path: Path, expected: int) -> Tuple[int, int, List[str]]:
    total = 0
    correct = 0
    errors: List[str] = []
    for f in _iter_executables(path):
        total += 1
        ok, res = _score_file(f)
        if ok:
            try:
                if int(res) == expected:
                    correct += 1
            except ValueError:
                errors.append(f"{f.name}: invalid label '{res}'")
        else:
            errors.append(f"{f.name}: {res}")
    return total, correct, errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate malware/goodware folders against running service")
    ap.add_argument("-m", "--malware", required=True, help="Path to malware folder or archive")
    ap.add_argument("-b", "--benign", required=True, help="Path to benign folder or archive")
    args = ap.parse_args()

    mal_src = Path(args.malware)
    ben_src = Path(args.benign)
    if not mal_src.exists():
        print(f"❌ Malware path not found: {mal_src}")
        return 2
    if not ben_src.exists():
        print(f"❌ Benign path not found: {ben_src}")
        return 2

    # Extract archives if needed
    cleanup: List[Path] = []
    try:
        mal_path = _extract_if_archive(mal_src)
        ben_path = _extract_if_archive(ben_src)
        if mal_path != mal_src:
            cleanup.append(mal_path)
        if ben_path != ben_src:
            cleanup.append(ben_path)

        print(f"🔴 Evaluating malware: {mal_path}")
        m_total, m_correct, m_err = _eval_folder(mal_path, expected=1)
        print(f"  Malware: {m_correct}/{m_total} correct")
        if m_err:
            print(f"  Errors (first 5): {', '.join(m_err[:5])}")

        print(f"🟢 Evaluating benign: {ben_path}")
        b_total, b_correct, b_err = _eval_folder(ben_path, expected=0)
        print(f"  Benign: {b_correct}/{b_total} correct")
        if b_err:
            print(f"  Errors (first 5): {', '.join(b_err[:5])}")

        total = m_total + b_total
        correct = m_correct + b_correct
        acc = (correct / total * 100.0) if total else 0.0
        print("")
        print(f"📊 Overall Accuracy: {acc:.1f}% ({correct}/{total})")
        return 0
    finally:
        for p in cleanup:
            try:
                shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())


