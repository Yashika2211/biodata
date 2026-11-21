"""Deck helpers: a small wrapper around python-pptx (titles, dataset tags, stat boxes, notes)."""
from __future__ import annotations

import os
import subprocess

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes, headlines, load

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
BLUE = RGBColor(0x00, 0x72, 0xB2)
ORANGE = RGBColor(0xD5, 0x5E, 0x00)
GREEN = RGBColor(0x00, 0x9E, 0x73)
GREY = RGBColor(0x55, 0x55, 0x55)
LIGHT = RGBColor(0xEE, 0xF3, 0xF8)
W, Hh = Inches(13.333), Inches(7.5)


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, Hh
        self.blank = self.prs.slide_layouts[6]

    def slide(self, title, notes, tag=None, number=True):
        s = self.prs.slides.add_slide(self.blank)
        if title:
            self.text(s, title, 0.6, 0.35, 7.4 if tag else 12.1, 0.9, size=28 if tag else 32, bold=True, color=NAVY)
            bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.22), Inches(1.2), Inches(0.07))
            bar.fill.solid(); bar.fill.fore_color.rgb = BLUE; bar.line.fill.background()
        if tag:
            pill = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.1), Inches(0.42), Inches(4.7), Inches(0.5))
            pill.fill.solid(); pill.fill.fore_color.rgb = LIGHT; pill.line.color.rgb = BLUE
            tf = pill.text_frame; tf.margin_left = tf.margin_right = Inches(0.08)
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = f"Dataset: {tag}"; r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = BLUE
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        s.notes_slide.notes_text_frame.text = notes
        return s

    def text(self, s, text, x, y, w, h, size=20, bold=False, color=GREY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
        lines = text if isinstance(text, list) else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            parts = line.split("**")
            for j, t in enumerate(parts):
                if not t:
                    continue
                r = p.add_run(); r.text = t
                r.font.size = Pt(size); r.font.bold = bold or (j % 2 == 1); r.font.color.rgb = color
            p.space_after = Pt(10)
        return tb

    def bullets(self, s, items, x, y, w, h, size=22):
        return self.text(s, ["•  " + t for t in items], x, y, w, h, size=size, color=RGBColor(0x22, 0x22, 0x22))

    def image(self, s, path, x, y, w=None, h=None):
        if not os.path.exists(path):
            return None
        kw = {}
        if w: kw["width"] = Inches(w)
        if h: kw["height"] = Inches(h)
        return s.shapes.add_picture(path, Inches(x), Inches(y), **kw)

    def stat(self, s, big, small, x, y, w=3.0, color=BLUE):
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(1.55))
        box.fill.solid(); box.fill.fore_color.rgb = LIGHT; box.line.fill.background()
        self.text(s, big, x, y + 0.08, w, 0.8, size=34, bold=True, color=color, align=PP_ALIGN.CENTER)
        self.text(s, small, x + 0.1, y + 0.85, w - 0.2, 0.7, size=14, color=GREY, align=PP_ALIGN.CENTER)

    def save(self, path):
        self.prs.save(path)
