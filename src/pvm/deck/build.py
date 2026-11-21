"""Assemble the 12-slide deck and (optionally) render it to PDF."""
from __future__ import annotations

import os
import subprocess
from types import SimpleNamespace

from ..docs_common import headlines, load
from . import (accuracy, adaptive, architecture, conclusion, cost, federated, latency, limitations,
               privacy_utility, problem, title)
from .helpers import Deck

SLIDES = [title, problem, architecture, adaptive, accuracy, federated, privacy_utility, latency, cost,
          limitations, conclusion]


def build(summary_path="results/summary.json", out="dist/ppt/deck.pptx"):
    S = load(summary_path)
    D = S["datasets"]
    first = "eicu" if "eicu" in D else next(iter(D))
    ctx = SimpleNamespace(S=S, D=D, H={k: headlines(S, k) for k in D}, first=first,
                          syn="synthetic" if "synthetic" in D else first)
    dk = Deck()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for sl in SLIDES:
        sl.add(dk, ctx)
    dk.save(out)
    return out


def to_pdf(pptx_path):
    outdir = os.path.dirname(pptx_path)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, pptx_path],
                   check=True, capture_output=True, timeout=240)
    return pptx_path.replace(".pptx", ".pdf")


def main():
    print(build())
