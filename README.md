# Plate

Print-grade data visualisation plates from [SubScout](https://github.com/AdmcCarthy/SubScout) stories: real paper sizes
(A4 to A0), vector PDF with live text and embedded fonts, PNG at a stated dpi, and consistent furniture (title, legend
slot, source / units / confidence strip, notes, declared exceptions). Static by design.

```
uv run plate render path/to/built-site --size a3-landscape --size a1-portrait --dpi 200 --density rich --legend rail
```

Input is a site built by SubScout (>= 0.5.0) in which chart blocks carry `export: true`; Plate reads each
`export/<id>/` payload, so SubScout's own chart components draw the figure. Output goes to `_out/plates/<id>/` with a
`manifest.json` (size, dpi, hash, QA findings, revision).

| Option | Meaning |
|---|---|
| `--size` | `a4`..`a0` (`-landscape` / `-portrait`), `slide`, `square`, `WxHmm`; repeatable |
| `--density standard\|rich` | `rich` adds a notes rail (notes, declared exception, confidence) |
| `--legend top\|rail\|bottom` | Named legend slot |
| `--dpi`, `--format` | PNG resolution (capped by `--max-mp`, default 20 MP; the PDF is the print product) and `pdf` / `png` |
| `--theme light\|dark` | Colour scheme; light for print |
| `--all-states` | Every story state, not only the final view |
| `--strict` | Exit 1 on any QA finding (text under 6 pt, overflow, missing source or confidence) |

Sizes at 300 dpi: A3 17 MP, A1 70 MP, A0 139 MP. Use the PDF for large sheets; PNG is a proof and is capped (large canvases also cost memory).

See `styleguide/print.md`. Part of a set: SubScout (stories) -> Plate (plates) -> Sheet (maps, built on Relief).
