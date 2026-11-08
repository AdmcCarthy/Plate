"""Render the export figures of a built SubScout site as print plates.

Input: a site folder built by SubScout (>= 0.5.0) with `export/<id>/index.html` pages. Those pages carry the
figure payload (the contract). Plate writes `plate/<id>/index.html` into a working copy of the site, renders it
in headless Chromium at the paper size, and writes into the output folder:

    <out>/<id>/<size>-<theme>-<state>.pdf   vector PDF, fonts embedded, exact paper size
    <out>/<id>/<size>-<theme>-<state>.png   raster at --dpi (capped by --max-mp)
    <out>/manifest.json                     every file, its size, dpi, hash, QA issues and provenance
"""

from __future__ import annotations

import datetime as dt
import functools
import hashlib
import html
import http.server
import json
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

import jinja2

from . import __version__, sizes

ASSETS = Path(__file__).parent / "assets"
TEMPLATES = Path(__file__).parent / "templates"
CONF = {
    "observed": "Observed: measured or published by the source and cited.",
    "derived": "Derived: our calculation from observed data; the method is stated.",
    "interpreted": "Interpreted: depends on a model or judgement; the range or assumption is given.",
}
LEVEL = {"observed": "Observed", "derived": "Derived", "interpreted": "Interpreted"}


def read_payload(page: Path) -> dict:
    text = page.read_text(encoding="utf-8")
    return json.loads(text.split('id="ss-payload">')[1].split("</script>")[0].replace("<\\/", "</"))


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "state"


def _git_rev(path: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return "unversioned"


def write_plate_page(work: Path, fig_id: str, export_html: Path, plate: dict, story_rev: str) -> Path:
    payload = read_payload(export_html)
    spec = payload["fig"]["spec"]
    fm_src = export_html.read_text(encoding="utf-8")
    fm = {
        "palette": (re.search(r'data-palette="([^"]*)"', fm_src) or [None, "tide"])[1],
        "surface": (re.search(r'data-surface="([^"]*)"', fm_src) or [None, "nordic-cool"])[1],
        "kicker": html.unescape((re.search(r'class="ex-kicker">([^<]*)<', fm_src) or [None, ""])[1]),
    }
    foot = re.findall(r"<span><b>([^<]*)</b>([^<]*)</span>", fm_src)
    facts = [(k, html.unescape(v)) for k, v in foot]
    credit = html.unescape((re.search(r'class="ex-credit">([^<]*)<', fm_src) or [None, ""])[1])
    today = dt.date.today().isoformat()
    facts.append(("Plate", f"{today} · {story_rev}"))
    conf = LEVEL.get(spec.get("confidence"), "")
    payload["plate"] = plate
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES), autoescape=False)
    page = env.get_template("plate.html.j2").render(
        fm=fm,
        spec=spec,
        facts=facts,
        credit=credit,
        esc=html.escape,
        plain_title=re.sub("<[^>]+>", "", spec.get("title", "")),
        conf_text=CONF.get(spec.get("confidence"), conf),
        payload=json.dumps(payload, ensure_ascii=False, default=str).replace("</", "<\\/"),
    )
    d = work / "plate" / fig_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page, encoding="utf-8")
    return d


def _serve(directory: Path):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a: Any) -> None:
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(directory)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def stamp_pdf(path: Path, title: str, subject: str, keywords: str) -> None:
    from pypdf import PdfReader, PdfWriter

    r = PdfReader(str(path))
    w = PdfWriter(clone_from=r)
    w.add_metadata(
        {
            "/Title": title,
            "/Author": "Adam McCarthy",
            "/Subject": subject,
            "/Keywords": keywords,
            "/Creator": f"Plate {__version__}",
            "/Producer": "Plate (Chromium)",
        }
    )
    with path.open("wb") as f:
        w.write(f)


def stamp_png(path: Path, dpi: int, meta: dict[str, str]) -> None:
    from PIL import Image, PngImagePlugin

    Image.MAX_IMAGE_PIXELS = None
    info = PngImagePlugin.PngInfo()
    for k, v in meta.items():
        info.add_text(k, v)
    with Image.open(path) as im:
        im.load()
        im.save(path, pnginfo=info, dpi=(dpi, dpi), optimize=False)


def _png_size(path: Path) -> list[int]:
    from PIL import Image

    with Image.open(path) as im:
        return list(im.size)


def render(
    site: Path,
    out: Path,
    size_names: list[str],
    themes: list[str] = ("light",),
    dpi: int = 200,
    formats: tuple[str, ...] = ("pdf", "png"),
    density: str = "standard",
    legend: str = "top",
    only: list[str] | None = None,
    zoom: float | None = None,
    min_pt: float = 6.0,
    max_mp: float = 120.0,
    all_states: bool = False,
) -> dict:
    from playwright.sync_api import sync_playwright

    site, out = Path(site).resolve(), Path(out).resolve()
    pages = sorted(p for p in (site / "export").glob("*/index.html"))
    if only:
        pages = [p for p in pages if p.parent.name in only]
    if not pages:
        raise SystemExit(f"no export pages in {site}/export (add `export: true` to a chart block, rebuild)")
    out.mkdir(parents=True, exist_ok=True)
    story_rev = _git_rev(site.parent)
    manifest: dict[str, Any] = {
        "plate": __version__,
        "site": str(site),
        "rendered": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "files": [],
    }
    with tempfile.TemporaryDirectory(prefix="plate-") as tmp:
        work = Path(tmp) / "site"
        # symlink the built site, write plate pages in a separate overlay served first
        shutil.copytree(site, work, symlinks=True, ignore=shutil.ignore_patterns("png", "*.png"))
        (work / "plate" / "_assets").mkdir(parents=True, exist_ok=True)
        for f in ASSETS.iterdir():
            shutil.copy2(f, work / "plate" / "_assets" / f.name)
        srv, url = _serve(work)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                for ep in pages:
                    fig_id = ep.parent.name
                    payload = read_payload(ep)
                    spec = payload["fig"]["spec"]
                    states = payload["states"] if all_states else payload["states"][-1:]
                    first_state = len(payload["states"]) - len(states)
                    for sname in size_names:
                        lay = sizes.layout(sizes.parse_size(sname), zoom)
                        plate_cfg = {**lay, "density": density, "legend": legend, "min_pt": min_pt}
                        write_plate_page(work, fig_id, ep, plate_cfg, story_rev)
                        mp = sizes.pixels_at(lay, dpi)
                        eff_dpi = dpi
                        if mp[0] * mp[1] / 1e6 > max_mp:
                            eff_dpi = int(dpi * (max_mp * 1e6 / (mp[0] * mp[1])) ** 0.5)
                        for theme in themes:
                            for i, st in enumerate(states, start=first_state):
                                ctx = browser.new_context(
                                    viewport={
                                        "width": int(lay["paper_w_px"]),
                                        "height": int(lay["paper_h_px"]),
                                    },
                                    device_scale_factor=min(eff_dpi / 96, 8),
                                )
                                pg = ctx.new_page()
                                errors: list[str] = []
                                pg.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
                                pg.goto(f"{url}plate/{fig_id}/?theme={theme}&state={i}")
                                pg.wait_for_function("document.body.dataset.ready === '1'", timeout=60000)
                                issues = pg.evaluate("window.__plateQA")
                                stem = f"{lay['name']}-{theme}-{slug(st['name'])}"
                                d = out / fig_id
                                d.mkdir(exist_ok=True)
                                title = re.sub("<[^>]+>", "", st["state"].get("title") or spec.get("title", ""))
                                rec_base = {
                                    "figure": fig_id,
                                    "size": lay["name"],
                                    "w_mm": lay["w_mm"],
                                    "h_mm": lay["h_mm"],
                                    "theme": theme,
                                    "state": st["name"],
                                    "zoom": lay["zoom"],
                                    "qa": issues,
                                    "errors": errors,
                                }
                                if "pdf" in formats:
                                    f = d / f"{stem}.pdf"
                                    pg.pdf(
                                        path=str(f),
                                        width=f"{lay['w_mm']}mm",
                                        height=f"{lay['h_mm']}mm",
                                        print_background=True,
                                        prefer_css_page_size=False,
                                        margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                                    )
                                    stamp_pdf(
                                        f,
                                        title,
                                        f"{spec.get('source', '')} · confidence: {spec.get('confidence', '')}",
                                        f"Plate, {fig_id}",
                                    )
                                    manifest["files"].append(
                                        {
                                            **rec_base,
                                            "file": str(f.relative_to(out)),
                                            "format": "pdf",
                                            "bytes": f.stat().st_size,
                                            "sha256": _sha(f),
                                        }
                                    )
                                if "png" in formats:
                                    f = d / f"{stem}.png"
                                    pg.screenshot(path=str(f), type="png")
                                    stamp_png(
                                        f,
                                        eff_dpi,
                                        {
                                            "Title": title,
                                            "Source": str(spec.get("source", "")),
                                            "Software": f"Plate {__version__}",
                                        },
                                    )
                                    manifest["files"].append(
                                        {
                                            **rec_base,
                                            "file": str(f.relative_to(out)),
                                            "format": "png",
                                            "dpi": eff_dpi,
                                            "dpi_requested": dpi,
                                            "px": _png_size(f),
                                            "bytes": f.stat().st_size,
                                            "sha256": _sha(f),
                                        }
                                    )
                                ctx.close()
                browser.close()
        finally:
            srv.shutdown()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    return manifest
