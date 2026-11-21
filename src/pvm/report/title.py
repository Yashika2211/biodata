"""Report section: title."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.p(TITLE, bold=True, size=19, align="center", after=2)
    doc.p(f"{AUTHOR}  ·  Big Data course project  ·  {datetime.date.today():%d %B %Y}", size=10.5,
          align="center", after=10)
