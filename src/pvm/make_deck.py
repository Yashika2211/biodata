"""Facade: ``python -m pvm.make_deck`` builds the deck (see ``pvm.deck``)."""
from .deck import build, main, to_pdf  # noqa: F401

if __name__ == "__main__":
    main()
