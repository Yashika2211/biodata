"""Assemble report.docx from section modules and convert it to PDF."""
from __future__ import annotations

import os
import subprocess
from types import SimpleNamespace

from ..docs_common import headlines, load
from . import (abstract, conclusion, limitations, method, problem, references, reproducibility,
               results, setup, title)
from .helpers import Doc

SECTIONS = [title, abstract, problem, method, setup, results, limitations, conclusion, reproducibility, references]


def build(summary_path="results/summary.json", out="dist/report/report.docx"):
    S = load(summary_path)
    D = S["datasets"]
    ctx = SimpleNamespace(S=S, D=D, syn=D.get("synthetic"), eic=D.get("eicu"),
                          H={k: headlines(S, k) for k in D}, P=S["protocol"])
    doc = Doc()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for sec in SECTIONS:
        sec.add(doc, ctx)
    doc.save(out)
    return out


def to_pdf(docx_path):
    outdir = os.path.dirname(docx_path)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path],
                   check=True, capture_output=True, timeout=180)
    return docx_path.replace(".docx", ".pdf")


def main():
    p = build()
    try:
        print(to_pdf(p))
    except Exception as e:                                     # LibreOffice is optional
        print("PDF conversion skipped:", e)
