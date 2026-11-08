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

## Idiom (private repo)

Idiom is Adam McCarthy's private repo (`github.com/AdmcCarthy/Idiom`; `gh repo clone AdmcCarthy/Idiom` with access, normally linked at
`../../shared/idiom`) of voice, house style, working rules and the lookup tables agents use first: `DIRECTORY.md` says which repo already
does a job, `DATASETS.md` gives every dataset's terms, attribution line and status. Read the relevant one before choosing a repo or
using data, and update it when you learn something new. Never copy anything from its `personal/` or `working/` folders into this repo
or quote it in public output; if the folder is not available, say so and carry on with this file.
