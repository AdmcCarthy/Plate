from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import sizes


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="plate", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="render the export figures of a built SubScout site")
    r.add_argument("site", type=Path)
    r.add_argument("--out", type=Path, default=Path("_out/plates"))
    r.add_argument(
        "--size",
        action="append",
        help="a4..a0[-landscape], slide, square, WxHmm (repeatable); default a3-landscape",
    )
    r.add_argument("--theme", action="append", choices=["light", "dark"])
    r.add_argument("--dpi", type=int, default=200)
    r.add_argument("--format", action="append", choices=["pdf", "png"])
    r.add_argument("--density", choices=["standard", "rich"], default="standard")
    r.add_argument("--legend", choices=["top", "rail", "bottom"], default="top")
    r.add_argument("--only", action="append", help="figure id (repeatable)")
    r.add_argument("--zoom", type=float, help="layout-to-paper zoom (default: automatic from sheet size)")
    r.add_argument("--min-pt", type=float, default=6.0)
    r.add_argument(
        "--max-mp", type=float, default=20.0, help="PNG size cap in megapixels (dpi is lowered to fit; use the PDF for print)"
    )
    r.add_argument("--all-states", action="store_true", help="render every story state, not just the final one")
    r.add_argument("--strict", action="store_true", help="exit 1 if any QA issue or page error is found")
    s = sub.add_parser("sizes", help="list paper sizes with pixel counts")
    s.add_argument("--dpi", type=int, default=300)
    return p


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if a.cmd == "sizes":
        for n in ["a4", "a3", "a2", "a1", "a0"]:
            s = sizes.parse_size(n)
            w, h = sizes.pixels_at(s, a.dpi)
            print(f"{n.upper():3} {s['w_mm']:.0f} x {s['h_mm']:.0f} mm  {w} x {h} px at {a.dpi} dpi  ({w * h / 1e6:.0f} MP)")
        return 0
    from .render import render

    m = render(
        a.site,
        a.out,
        a.size or ["a3-landscape"],
        a.theme or ["light"],
        a.dpi,
        tuple(a.format or ["pdf", "png"]),
        a.density,
        a.legend,
        a.only,
        a.zoom,
        a.min_pt,
        a.max_mp,
        all_states=a.all_states,
    )
    bad = 0
    for f in m["files"]:
        flag = f" QA:{len(f['qa'])}" if f["qa"] else ""
        bad += len(f["qa"]) + len(f["errors"])
        print(f"{f['file']}  {f['bytes'] / 1e6:.1f} MB{flag}")
        for i in f["qa"][:6]:
            print("   ", i)
    return 1 if (a.strict and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
