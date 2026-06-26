# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-06-26

### Added

- **In-browser live code via Pyodide** — `live_code.runtime: auto | jupyter |
  pyodide`. `pyodide` runs Python in the browser (WebAssembly), so runnable
  blocks work on a published static site with no server; `auto` uses Jupyter when
  reachable and falls back to Pyodide. Configure WASM-wheel packages via
  `live_code.pyodide.packages`. (Python only; shell blocks need Jupyter.)
- **`symbols.decorator_labels`** — rewrite the text of mkdocstrings decorator
  labels (`property` → `prop`, …) via a build-time pass, in headings and the TOC.

[0.3.0]: https://github.com/ryanrudes/richdocs/releases/tag/v0.3.0

## [0.2.0] - 2026-06-26

Deep configurability for badges, linking, and highlighting. All additions are
override-only — defaults reproduce the 0.1.0 look exactly.

### Added

- **`symbols.labels`** — relabel any API symbol-kind badge (`class` → `def` /
  `dataclass` / `enum` / `member` / anything) in both headings and the TOC.
- **`symbols.colors`** — set `{fg, bg}` per kind; also recolors the decorator
  labels that map to a kind (e.g. `property` follows `attribute`).
- **`api.linkify`** — `short_names`, `dotted`, `skip_extensions`, and custom
  `aliases` (map an arbitrary word to a symbol) for both prose and code-block
  linking.
- **`theme.highlight`** — Shiki `theme`, `inline`, `default_language`,
  `languages`, and `aliases`.
- **`toc`** — `collapse_default` and `scrollspy_offset`.

[0.2.0]: https://github.com/ryanrudes/richdocs/releases/tag/v0.2.0

## [0.1.0] - 2026-06-26

Initial release. richdocs began as the bespoke docs machinery of the
[retarget](https://github.com/ryanrudes/retarget) project and was extracted into
a standalone, configurable MkDocs Material plugin.

### Added

- Single `richdocs` MkDocs plugin entry point that wires up the whole experience
  (no manual `extra_css` / `extra_javascript` / `custom_templates`).
- Typed, validated config schema (`api`, `live_code`, `theme`, `features`);
  only `package` is required.
- Shiki syntax highlighting (default theme: VS Code "Shades of Purple") for code
  blocks and inline code.
- Runnable live-code blocks backed by a local Jupyter kernel (dev only).
- API-symbol hover tooltips + click-to-navigate in code blocks, and automatic
  linking of inline `` `Symbol` `` mentions to the mkdocstrings reference.
- mkdocstrings template overrides: enums render as `enum` / `member`; decorator
  badges (`property`, `classmethod`, …) in headings and the TOC.
- Collapsible in-page TOC sections and a scroll-spy tuned for long API pages.
- Themeable palette via `theme.palette` (friendly keys or raw `--rd-*` tokens),
  generated into a stylesheet at build time.
- Canonical API page derived from nav order, with `page_priority_overrides`.

### Fixed

- API-symbol hover state is reset on Material instant navigation (stale hover /
  orphaned tooltips after navigating between pages).
- Inline-link short-name tie-breaks are now deterministic across builds.

[Unreleased]: https://github.com/ryanrudes/richdocs/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ryanrudes/richdocs/releases/tag/v0.1.0
