"""Report section: repro."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("7  Reproducibility", 1)
    doc.p("Code: `code.zip` / the project repository. `make test` (unit tests), `make up` (two Kafka clusters), "
          "`make data` (download the open eICU demo), `make experiments` (both datasets, 5 seeds, ablations, benchmarks, "
          "`results/summary.json`), `make figures`, `make docs` (this report and the deck are generated from "
          "`results/summary.json`; no result is typed by hand). Environment: Python 3.11, Java 17, PySpark 3.5.3, pandas 2.2, "
          "`apache/kafka` 3.8.0. Seeds 0–4. Data are not redistributed; see `data/README.md`.")
