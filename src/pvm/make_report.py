"""Facade: ``python -m pvm.make_report`` builds the report (see ``pvm.report``)."""
from .report import build, main, to_pdf  # noqa: F401

if __name__ == "__main__":
    main()
