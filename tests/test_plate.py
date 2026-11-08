import json
import subprocess
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

from plate import sizes
from plate.render import render

FIX = Path(__file__).parent / "fixture"


def test_iso_sizes_and_pixels():
    a3 = sizes.parse_size("a3-landscape")
    assert (a3["w_mm"], a3["h_mm"]) == (420, 297)
    assert sizes.pixels_at(sizes.parse_size("a3"), 300) == (3508, 4961)
    assert sizes.pixels_at(sizes.parse_size("a0"), 300) == (9933, 14043)
    assert sizes.parse_size("500x700mm")["h_mm"] == 700
    with pytest.raises(ValueError):
        sizes.parse_size("a9")


def test_layout_zoom_keeps_layout_width_near_a3():
    assert sizes.layout(sizes.parse_size("a3-landscape"))["zoom"] == 1.0
    a1 = sizes.layout(sizes.parse_size("a1-portrait"))
    assert a1["zoom"] == pytest.approx(2.0, abs=0.01)
    assert 1100 < a1["w"] < 1200  # a1 portrait lays out like a3 portrait


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    exe = Path(sys.executable).parent / "subscout"
    subprocess.run([str(exe), "build", str(FIX), "--out", str(out)], check=True, capture_output=True)
    return out


@pytest.fixture(scope="module")
def rendered(site, tmp_path_factory):
    out = tmp_path_factory.mktemp("plates")
    m = render(site, out, ["a3-landscape", "a1-portrait"], dpi=60, density="rich", legend="rail")
    return out, m


def test_pdf_is_exact_paper_size_with_metadata_and_live_text(rendered):
    out, m = rendered
    pdfs = [f for f in m["files"] if f["format"] == "pdf" and f["size"] == "a1-portrait"]
    assert pdfs
    r = PdfReader(str(out / pdfs[0]["file"]))
    w, h = (float(x) / 72 * 25.4 for x in r.pages[0].mediabox[2:])
    assert (round(w), round(h)) == (594, 841)
    assert len(r.pages) == 1
    assert r.metadata.author == "Adam McCarthy"
    assert "Source" in r.pages[0].extract_text() or "SOURCE" in r.pages[0].extract_text()


def test_png_dpi_and_pixels(rendered):
    out, m = rendered
    from PIL import Image

    f = next(f for f in m["files"] if f["format"] == "png" and f["size"] == "a3-landscape")
    with Image.open(out / f["file"]) as im:
        assert im.size == tuple(f["px"]) and abs(im.size[0] - 992) <= 1
        assert round(im.info["dpi"][0]) == 60


def test_qa_clean_and_manifest(rendered):
    out, m = rendered
    assert all(not f["errors"] for f in m["files"])
    bad = [(f["file"], f["qa"]) for f in m["files"] if f["qa"]]
    assert not bad, bad
    assert json.loads((out / "manifest.json").read_text())["files"]
