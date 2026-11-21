"""Shared figure style: palette, dataset labels, save helpers."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


FIG = "figures"
DS_LABEL = {"synthetic": "Synthetic cohort", "eicu": "eICU-CRD demo + injected episodes"}
COL = {"A": "#9a9a9a", "A2": "#6b6b6b", "B": "#e69f00", "C": "#56b4e9", "D": "#0072b2",
       "E": "#cc79a7", "F": "#009e73", "G": "#d55e00"}
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 12, "axes.labelsize": 11, "figure.dpi": 100,
                     "savefig.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False})


def _save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name)
    fig.savefig(p)
    plt.close(fig)
    return p




def _load(path="results/summary.json"):
    return json.load(open(path))


def _m(d, key, metric):
    v = d["methods"][key][metric]
    return v["mean"], v["sd"]
