import os

import numpy as np
import pytest

from pvm import figs
from pvm.data.synthetic import make_patient
from pvm.figs import adaptive_example, style


def test_adaptive_example_renders_and_counts_alarms(tmp_path, monkeypatch):
    monkeypatch.setattr(style, "FIG", str(tmp_path))
    p = make_patient("x", "s", "copd", 4.0, np.random.default_rng(4))
    path, info = adaptive_example.plot_adaptive_example(p, "test", "ex.png")
    assert os.path.exists(path)
    assert info["static_alarms"] > 5 * max(info["adaptive_alarms"], 1)      # the whole point


def test_architecture_renders(tmp_path):
    out = figs.fig_architecture(str(tmp_path / "arch.png"))
    assert os.path.getsize(out) > 10_000
