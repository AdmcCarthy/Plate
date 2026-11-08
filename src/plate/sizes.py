"""Page sizes in millimetres (ISO 216 A series plus a few presets) and the layout/zoom model.

A plate is laid out on an artboard of *layout pixels* (CSS px, 96 per inch) and then scaled to the paper by a
zoom factor, so type and chart code that think in pixels still land at a sensible physical size on A1 or A0.
Layout width is kept near A3's 420 mm (1587 px) however large the sheet.
"""

from __future__ import annotations

MM_PER_IN = 25.4
CSS_PX_PER_IN = 96
REFERENCE_LONG_EDGE_MM = 420  # A3: the layout size every sheet is scaled from

ISO = {"a4": (210, 297), "a3": (297, 420), "a2": (420, 594), "a1": (594, 841), "a0": (841, 1189)}
PRESETS = {"slide": (338.67, 190.5), "square": (300, 300)}  # 16:9 slide at 96 dpi = 1280 x 720 px


def mm_to_px(mm: float) -> float:
    return mm / MM_PER_IN * CSS_PX_PER_IN


def parse_size(name: str) -> dict:
    """'a3', 'a3-landscape', 'a1-portrait', 'slide', or 'WxHmm' (e.g. '500x700mm')."""
    n = name.lower().strip()
    if n.endswith("mm") and "x" in n:
        w, h = (float(v) for v in n[:-2].split("x"))
        return {"name": n, "w_mm": w, "h_mm": h}
    base, _, orient = n.partition("-")
    if base in PRESETS:
        w, h = PRESETS[base]
    elif base in ISO:
        w, h = ISO[base]
        if orient in ("", "portrait"):
            orient = orient or "portrait"
        if orient == "landscape":
            w, h = h, w
    else:
        raise ValueError(f"unknown size {name!r}; try a4..a0 (-landscape/-portrait), slide, square or 500x700mm")
    return {"name": n, "w_mm": w, "h_mm": h}


def layout(size: dict, zoom: float | None = None) -> dict:
    """Artboard in layout px, the zoom to paper, and the paper size in px at 96 dpi."""
    w_mm, h_mm = size["w_mm"], size["h_mm"]
    z = zoom or max(1.0, max(w_mm, h_mm) / REFERENCE_LONG_EDGE_MM)
    return {
        **size,
        "zoom": round(z, 4),
        "w": round(mm_to_px(w_mm) / z),
        "h": round(mm_to_px(h_mm) / z),
        "paper_w_px": mm_to_px(w_mm),
        "paper_h_px": mm_to_px(h_mm),
    }


def pixels_at(size: dict, dpi: int) -> tuple[int, int]:
    return round(size["w_mm"] / MM_PER_IN * dpi), round(size["h_mm"] / MM_PER_IN * dpi)
