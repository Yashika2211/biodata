"""Word-document helpers (styles, tables, figures) and small formatting utilities."""
from __future__ import annotations

import datetime
import os
import subprocess

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from ..docs_common import (DS_NAME, METHOD_NAME, ci, eps_str, fmt_bytes, headlines, load, num, pm)

AUTHOR = "Yashika Bhatia"
TITLE = "Privacy-Preserving Patient Vitals Monitoring: A Kafka + Spark Streaming Study"


def verdict(p, higher_better=True):
    """Describe a paired difference by its 95% CI."""
    if p.get("ci95") is None:
        return "is not estimable"
    lo, hi = p["ci95"]
    if lo <= 0 <= hi:
        return "is statistically indistinguishable from"
    good = (p["mean"] > 0) == higher_better
    return "is significantly better than" if good else "is significantly worse than"


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


class Doc:
    def __init__(self):
        self.d = Document()
        s = self.d.sections[0]
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin = s.right_margin = Cm(2.1)
        s.top_margin = s.bottom_margin = Cm(2.0)
        st = self.d.styles["Normal"]
        st.font.name = "Calibri"; st.font.size = Pt(10.5)
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.line_spacing = 1.08
        for name, size in (("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11)):
            h = self.d.styles[name]
            h.font.name = "Calibri"; h.font.size = Pt(size); h.font.bold = True
            h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
            h.paragraph_format.space_before = Pt(10 if name != "Heading 1" else 14)
            h.paragraph_format.space_after = Pt(4)
        self.fig_n = 0
        self.tab_n = 0

    def h(self, text, lvl=1):
        return self.d.add_heading(text, lvl)

    def p(self, text="", bold=False, italic=False, size=None, align=None, after=None):
        para = self.d.add_paragraph()
        self._runs(para, text, bold, italic, size)
        if align == "center":
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if after is not None:
            para.paragraph_format.space_after = Pt(after)
        return para

    def _runs(self, para, text, bold=False, italic=False, size=None):
        parts = text.split("**")
        for i, t in enumerate(parts):
            if not t:
                continue
            r = para.add_run(t)
            r.bold = bold or (i % 2 == 1)
            r.italic = italic
            if size:
                r.font.size = Pt(size)

    def bullets(self, items):
        for t in items:
            para = self.d.add_paragraph(style="List Bullet")
            self._runs(para, t)
            para.paragraph_format.space_after = Pt(2)

    def figure(self, path, caption, width=16.0):
        if not path or not os.path.exists(path):
            return
        self.fig_n += 1
        self.d.add_picture(path, width=Cm(width))
        self.d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c = self.p(f"Figure {self.fig_n}. {caption}", italic=True, size=9, align="center", after=8)
        return c

    def table(self, header, rows, caption, widths=None, size=8.5, bold_rows=()):
        self.tab_n += 1
        self.p(f"Table {self.tab_n}. {caption}", italic=True, size=9, after=2)
        t = self.d.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, htxt in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = ""
            r = c.paragraphs[0].add_run(htxt); r.bold = True; r.font.size = Pt(size)
            shade(c, "DCE6F1")
        for ri, row in enumerate(rows):
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
                r.bold = ri in bold_rows
                if i > 0:
                    cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Cm(w)
        for row in t.rows:
            for c in row.cells:
                for para in c.paragraphs:
                    para.paragraph_format.space_after = Pt(0)
        self.d.add_paragraph().paragraph_format.space_after = Pt(2)
        return t

    def save(self, path):
        self.d.save(path)


def accuracy_rows(d):
    rows = []
    keys = ["A", "A2", "B", "C", "D", "E", "F"] + [r["key"] for r in sorted(d["privacy_utility"], key=lambda r: r["sigma"])]
    for k in keys:
        m = d["methods"][k]
        name = METHOD_NAME.get(k) or f"G  FL + DP, σ={float(k[2:]):g} (ε={eps_str(m['epsilon']['mean'])})"
        rows.append([name, pm(m["precision"]), pm(m["recall"]), pm(m["f1"]), pm(m["fa_per_day"]),
                     pm(m["delay_min"], 0), pm(m["auroc"]), pm(m["auprc"])])
    return rows
