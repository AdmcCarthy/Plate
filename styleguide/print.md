# Print plates

Extends the SubScout style guide (language, rules, uncertainty) for paper and PDF. Public.

## Sheet and type
- Real sheet sizes in millimetres (ISO A4-A0, landscape or portrait; slide, square, custom `WxHmm`).
- Plates are laid out on an A3-sized artboard (1587 px long edge) and scaled to the sheet, so type grows on A1 and A0
  rather than the figure getting emptier. Use `--zoom` to override.
- Type no smaller than 6 pt on paper (checked, `--min-pt`). Text stays live in the PDF (selectable, embedded fonts).

## Furniture
- Header: kicker, action title (the finding), subtitle (what is plotted, units, period).
- Legend in one of three named slots: `top` (under the title, the default), `rail` (right column), `bottom`.
  Keep one slot per series of plates so a set reads as a set.
- Footer strip on every plate: Source (with date), Units, Confidence, Plate (date and revision), credit.
- `rich` density adds a right rail with notes, the declared exception and the confidence definition. Use it for
  A2 and above or for plates meant to stand alone.

## Truth gate on paper
- The truth gate (rules.md) is unchanged. Sheet size never justifies cropping an axis or dropping uncertainty.
- Every plate records its provenance in the manifest: file hash, size, dpi, QA findings, story revision.

## Static first
- The deliverable is a file: PDF (vector), PNG at a stated dpi, or both. Interaction belongs to the story page.
- Large files are not committed; they are rendered in CI or locally and attached to releases. The manifest is committed.

## Canvas figures
- Figures drawn on canvas (dense layers such as Tulip's bulb) are rasterised inside the PDF at `opts.pixelRatio` device
  pixels per layout pixel; vector parts (labels, axes, legend, furniture) stay vector. Figures should size canvases with
  `opts.pixelRatio` and skip ahead-painting of other story states when `opts.export` is set.
