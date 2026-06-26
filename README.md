<div align="center">

# richdocs

**A batteries-included documentation experience for [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).**

Shiki syntax highlighting · runnable live code · API-symbol hover & auto-linking · mkdocstrings enum/decorator badges · a polished collapsible TOC — all from a single plugin entry.

[![PyPI](https://img.shields.io/pypi/v/richdocs.svg)](https://pypi.org/project/richdocs/)
[![Python](https://img.shields.io/pypi/pyversions/richdocs.svg)](https://pypi.org/project/richdocs/)
[![CI](https://github.com/ryanrudes/richdocs/actions/workflows/ci.yml/badge.svg)](https://github.com/ryanrudes/richdocs/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

[**Live demo →**](https://ryanrudes.github.io/richdocs/)

</div>

---

## Why

MkDocs Material is excellent, but a *great* API-docs site usually means hand-wiring a pile of hooks, JavaScript, CSS, and mkdocstrings template overrides — and then re-doing it for the next project. **richdocs** packages that whole experience into one configurable plugin. The default look is the VS Code **"Shades of Purple"** theme; everything is overridable.

## Features

- 🎨 **Shiki syntax highlighting** — VS Code-accurate highlighting at runtime (the default theme is *Shades of Purple*), in both code blocks and inline code.
- ▶️ **Runnable live code** — execute Python/shell blocks against a local Jupyter kernel, right in the page (dev only).
- 🔗 **API-symbol hover & auto-linking** — inline `` `Symbol` `` mentions link to your mkdocstrings reference automatically, and hovering symbols in code blocks shows rich tooltips; click to jump.
- 🏷️ **Smarter mkdocstrings rendering** — enums render as `enum` / `member`, and headings & the TOC show decorator badges (`property`, `classmethod`, …).
- 🧭 **Polished TOC** — scroll-spy tuned for long API pages, plus collapsible sections that expand on demand.
- 🌈 **One dark palette, fully themeable** — override any color or the Shiki theme from `mkdocs.yml`.

## Install

```bash
pip install richdocs
```

`richdocs` pulls in `mkdocs-material` and `mkdocstrings[python]`, so that's all you need.

## Quickstart

Add the plugin to `mkdocs.yml` — the only required option is the package you're documenting:

```yaml
theme:
  name: material
  palette:
    scheme: slate          # richdocs ships a single dark scheme

plugins:
  - search
  - richdocs:              # ← list BEFORE mkdocstrings
      package: your_package
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
```

That's it. The plugin registers its stylesheets/scripts, points mkdocstrings at its templates, indexes your API, and serves the Shiki theme — no `extra_css` / `extra_javascript` / `custom_templates` plumbing required.

> **Ordering:** list `richdocs` **before** `mkdocstrings` so its enum/badge templates take effect.

## Configuration

Everything except `package` is optional and has sensible defaults:

```yaml
plugins:
  - richdocs:
      package: your_package        # required: the Python package to document & index

      api:
        id_prefix: your_package     # mkdocstrings anchor prefix (default: = package)
        page_priority_overrides: {} # {"/api/reference/": 100, ...} canonical-page tuning
        registry_exports: {}        # {name: "pkg.module.singleton"} for registry singletons
        ambiguous_short_names: []   # short names to never auto-link
        prefer_class_for_short: {}  # {short_name: ClassName} to disambiguate
        short_name_blocklist: []
        extra_modules: []           # extra submodules whose __all__ to index
        section_suffixes: ["-functions", "-attributes", "-classes"]
        linkify:                    # what / how symbols get linked
          short_names: true         # link `Robot`, not just `pkg.Robot`
          dotted: true              # resolve `fmt.joint_names` via the rightmost segment
          skip_extensions: [md, py, yaml, yml, npz, json, toml, txt]
          aliases: {}               # {"the result": "pkg.RetargetingResult"}

      symbols:                      # relabel / recolor API badges (override-only)
        labels: {}                  # {function: def, attribute: var, enum: enum, ...}
        colors: {}                  # {enum: {fg: "#7ee8d3", bg: "#7ee8d324"}, class: {fg: "#b362ff"}, ...}
        decorator_labels: {}        # rewrite decorator-label text {property: prop, classmethod: cls}

      live_code:                    # runnable code blocks
        enabled: true
        runtime: jupyter            # jupyter (local) | pyodide (browser) | auto
        jupyter_url: http://127.0.0.1:8888/
        token: your_package-docs    # default: <package>-docs
        launcher_port: 8889
        launcher_script: scripts/docs-jupyter.sh
        kernel: python3
        runnable_languages: [python, bash]
        pyodide:                    # in-browser Python (works on a published static site)
          version: "0.27.2"
          packages: []              # WASM-wheel packages to install, e.g. [numpy, pandas]

      theme:
        palette: {}                 # override any color (see Theming)
        layout: {}                  # TOC spacing tokens
        highlight:                  # Shiki syntax highlighting
          theme: shades-of-purple   # bundled id, or path to a Shiki theme JSON
          inline: true              # highlight inline code too
          default_language: python  # for untagged fenced blocks
          languages: [python, bash, yaml, toml, json, markdown]
          aliases: {py: python, sh: bash, yml: yaml}

      toc:
        collapse_default: true      # nested API/category sections start collapsed
        scrollspy_offset: 0         # extra px added to the active-heading threshold

      features:                     # coarse on/off
        shiki: true
        api_hover: true
        linkify_inline_code: true
        toc_collapsible: true
        toc_scrollspy: true
        hide_empty_toc: true
```

### Theming

Override individual palette colors with friendly keys (or any raw `--rd-*` CSS custom property):

```yaml
plugins:
  - richdocs:
      package: your_package
      theme:
        palette:
          page_bg: "#1e1e3f"
          code_bg: "#2d2b55"
          sidebar_bg: "#222244"
          gold: "#fad000"          # accent
          purple_bright: "#b362ff" # links
          # ...or a raw token:
          "--rd-text-muted": "#a599e9"
```

Supported friendly keys: `page_bg`, `sidebar_bg`, `code_bg`, `code_fg`, `surface_1`–`surface_4`, `text`, `text_muted`, `text_soft`, `purple`, `purple_bright`, `gold`/`accent`, `enum_fg`/`enum_bg`, `member_fg`/`member_bg`, and the TOC layout tokens `toc_row_gap`, `toc_branch_gap`, `toc_section_gap`, `toc_link_min_height`.

### Symbol labels & colors

Rename or recolor the API symbol-kind badges (headings **and** TOC) per construct
— override-only, so unset kinds keep the bundled defaults:

```yaml
plugins:
  - richdocs:
      package: your_package
      symbols:
        labels:
          function: def          # "" empties the badge
          attribute: var
          enum: enum
          member: member
        colors:
          enum:  { fg: "#7ee8d3", bg: "#7ee8d324" }
          class: { fg: "#b362ff" }
```

Recognized kinds: `module`, `class`, `enum`, `function`, `method`, `attribute`,
`type_alias`, `member`. Setting a kind's color also recolors the decorator labels
that map to it (e.g. `property` follows `attribute`). Dataclasses keep griffe's
built-in `dataclass` label out of the box; recolor them via the `class` kind.

You can also rewrite the **text** of mkdocstrings' decorator labels (these come
from griffe, so they're handled by a build-time pass rather than the badge CSS):

```yaml
plugins:
  - richdocs:
      package: your_package
      symbols:
        decorator_labels: { property: prop, classmethod: cls, staticmethod: static }
```

## Live code: local Jupyter or in-browser Pyodide

Runnable code blocks have two backends, chosen by `live_code.runtime`:

- **`jupyter`** (default) — a local Jupyter kernel (full Python, any package).
  On a published site it shows a "needs Jupyter" notice rather than running.
- **`pyodide`** — CPython compiled to WebAssembly, running **in the browser**, so
  blocks are runnable on a published static site (e.g. GitHub Pages) with no
  server. Python only (shell blocks need Jupyter); install WASM-wheel packages via
  `live_code.pyodide.packages` (e.g. `numpy`, `pandas` — not `torch`/`mujoco`).
- **`auto`** — use Jupyter if it's reachable, otherwise fall back to Pyodide.

> **Opt into web execution deliberately.** Pyodide can only run browser-compatible
> code — crucially, **your own package usually isn't available in the browser**, so
> blocks that `import your_package` will fail under `pyodide`/`auto`. Use them only
> when your runnable blocks are stdlib- or WASM-wheel-only. That's why the default
> is `jupyter`.

```yaml
plugins:
  - richdocs:
      package: your_package
      live_code:
        runtime: auto
        pyodide:
          packages: [numpy]
```

## How it works

A single `RichDocsPlugin` (MkDocs entry point) replaces what used to be four build hooks plus scattered asset wiring:

| Event | What it does |
| --- | --- |
| `on_config` | validates config, derives defaults, registers bundled CSS/JS, points mkdocstrings at the templates |
| `on_files` | emits `richdocs-config.js` (`window.__richdocsConfig`, read by the JS) and `richdocs-palette.css` (your overrides) |
| `on_page_markdown` | auto-links inline `` `Symbol` `` mentions to the API reference |
| `on_post_build` | scans the built site to index API anchors (`javascripts/api-symbols.json`) and injects decorator badges into the TOC |
| `on_serve` | runs a tiny local helper so the page can launch Jupyter for live code |

## Requirements

- Python 3.11+
- MkDocs Material 9.5+
- mkdocstrings[python] 0.25+ (for the API features)

## Development

```bash
git clone https://github.com/ryanrudes/richdocs
cd richdocs
uv venv && uv pip install -e ".[dev]"
uv run pytest        # unit tests
uv run ruff check .  # lint
```

## License

[Apache-2.0](LICENSE) © Ryan Rudes
