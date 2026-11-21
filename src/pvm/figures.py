"""Facade: ``python -m pvm.figures`` regenerates every figure (see ``pvm.figs``)."""
from .figs import *          # noqa: F401,F403
from .figs import make_all
from .figs.style import _load  # noqa: F401

if __name__ == "__main__":
    make_all()
