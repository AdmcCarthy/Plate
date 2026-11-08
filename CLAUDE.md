# Plate: working rules

@../../shared/idiom/CORE.md

Print-grade plates from SubScout export payloads. Owner: Adam McCarthy. Public repo: **never copy anything from the
private Idiom repo into here** except files listed in its `public-manifest.txt` (`vendor/idiom/`, via its sync script).

- Dependencies run one way: Plate -> SubScout (pinned tag, dev group and at render time via the built site). SubScout
  must not depend on Plate. Sheet depends on Plate.
- Plate does not draw charts itself; it lays out furniture and reuses the built site's `runtime/` chart code.
- `uv run pytest` (builds a fixture story with SubScout, renders A3 and A1, checks PDF size, metadata, text, dpi, QA).
- Look at a rendered plate before calling a change done. `styleguide/print.md` is the print authority.
- Static first. Large outputs are not committed (see print.md).
