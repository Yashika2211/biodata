"""Build dist/code.zip, dist/report.zip, dist/ppt.zip (each must be < 20 MB) and verify them."""
from __future__ import annotations

import os
import subprocess
import sys
import zipfile

LIMIT = 20 * 1024 * 1024
EXCLUDE_DIRS = {".venv", ".venv-spark", "__pycache__", ".pytest_cache", "dist", "checkpoints", ".git",
                "spark-warehouse", "metastore_db", ".ipynb_checkpoints"}
EXCLUDE_TOP = {"data"}            # data files are never shipped (data/README.md is)
EXCLUDE_SUFFIX = (".pyc", ".gz", ".csv", ".zip", ".DS_Store")


def zip_code(path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            if root == ".":
                dirs[:] = [d for d in dirs if d not in EXCLUDE_TOP]
            for f in files:
                p = os.path.join(root, f)
                if f.endswith(EXCLUDE_SUFFIX) or p.startswith("./results/log_") or "v1_10s" in f:
                    continue
                z.write(p, os.path.join("code", os.path.relpath(p, ".")))
        z.write("data/README.md", "code/data/README.md")


def zip_files(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.basename(f))


def verify(path):
    size = os.path.getsize(path)
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        n = len(z.namelist())
    ok = bad is None and size < LIMIT
    print(f"{'OK ' if ok else 'BAD'} {path}: {size/1e6:.2f} MB, {n} files")
    return ok


def main():
    os.makedirs("dist", exist_ok=True)
    zip_code("dist/code.zip")
    zip_files("dist/report.zip", ["dist/report/report.docx", "dist/report/report.pdf"])
    zip_files("dist/ppt.zip", ["dist/ppt/deck.pptx"])
    ok = all(verify(p) for p in ("dist/code.zip", "dist/report.zip", "dist/ppt.zip"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
