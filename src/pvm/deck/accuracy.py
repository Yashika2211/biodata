"""Slide: accuracy."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    for ds in ([syn] + ([first] if first != syn else [])):
        h = H[ds]; d = D[ds]; n = 5 if ds == syn else 6
        s = dk.slide(f"Accuracy: adaptive features beat fixed thresholds",
                     f"{DS_NAME[ds]}. Static thresholds A and A2 produce {h['fa_A']:.1f} and {h['fa_A2']:.1f} false alarms per patient-day. "
                     f"The adaptive threshold alone, method C, brings this to {h['fa_C']:.2f}. Machine learning on adaptive features, D, has F1 "
                     f"{h['f1']['D']:.2f}. Mean and standard deviation over {d['n_seeds']} seeds, last 40 percent of each series held out. "
                     f"B versus D isolates the adaptive features: AUPRC difference {ci(h['D_B']['auprc'])}, F1 difference {ci(h['D_B']['f1'])}. "
                     "Report both honestly: at the tuned operating point the F1 gain is within noise even though ranking quality (AUPRC) improves. "
                     "Labels are injected episodes.", tag=DS_NAME[ds])
        dk.image(s, f"figures/fig_accuracy_{ds}.png", 0.5, 1.45, w=8.6)
        dk.stat(s, f"−{h['fa_cut_C_vs_A2']*100:.0f}%", "false alarms: adaptive threshold vs static + persistence", 9.4, 1.5, 3.4, GREEN)
        dk.stat(s, f"{h['f1']['D']:.2f}", f"F1, ML on adaptive features (static: {h['f1']['A2']:.2f})", 9.4, 3.2, 3.4, BLUE)
        dk.stat(s, f"{h['fa_A2']:.1f} → {h['fa_D']:.2f}", "false alarms / patient-day, A2 → D", 9.4, 4.9, 3.4, ORANGE)
