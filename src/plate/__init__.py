"""Plate: print-grade data visualisation plates."""

__version__ = "0.1.0"


def main() -> None:
    from .cli import main as _main

    raise SystemExit(_main())
