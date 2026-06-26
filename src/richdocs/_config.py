"""Typed, validated config schema for the ``richdocs`` plugin.

Only ``package`` is required; everything else has sensible defaults that
reproduce the bundled Shades-of-Purple look. The nested groups
(``api`` / ``symbols`` / ``live_code`` / ``theme`` / ``toc`` / ``features``)
keep the surface discoverable and self-documenting.
"""

from __future__ import annotations

from mkdocs.config import base
from mkdocs.config import config_options as c

# Default inline-code spans that are NOT treated as linkable symbols.
_DEFAULT_SKIP_EXTENSIONS = ["md", "py", "yaml", "yml", "npz", "json", "toml", "txt"]
# Default Shiki grammars to preload, and language aliases.
_DEFAULT_LANGUAGES = ["python", "bash", "yaml", "toml", "json", "markdown", "text", "plaintext"]
_DEFAULT_LANG_ALIASES = {"py": "python", "sh": "bash", "shell": "bash", "yml": "yaml", "md": "markdown"}


class LinkifyConfig(base.Config):
    """Fine-grained control over what inline/code symbols get auto-linked."""

    # Link bare short names (`Robot`) — not just fully-qualified `pkg.Robot`.
    short_names = c.Type(bool, default=True)
    # Resolve dotted expressions (`fmt.joint_names`) via the rightmost segment.
    dotted = c.Type(bool, default=True)
    # Inline-code spans matching these file extensions are never linked.
    skip_extensions = c.ListOfItems(c.Type(str), default=_DEFAULT_SKIP_EXTENSIONS)
    # Custom aliases: map an arbitrary word to a fully-qualified anchor id, e.g.
    # ``{"the result": "pkg.RetargetingResult"}``.
    aliases = c.Type(dict, default={})


class ApiConfig(base.Config):
    """API-symbol indexing, code-block hover, and inline auto-linking."""

    # mkdocstrings anchor-id prefix. Defaults to ``package`` (anchors are the
    # fully-qualified Python paths, which start with the top-level package).
    id_prefix = c.Optional(c.Type(str))
    # Per-page canonical-page preference. Maps a page-URL suffix (e.g.
    # ``/api/models/``) to an integer; lower = preferred when a symbol is
    # documented on several pages. Merged over the nav-derived defaults.
    page_priority_overrides = c.Type(dict, default={})
    # Registry singletons (no stable qualname) → their mkdocstrings anchor id.
    registry_exports = c.Type(dict, default={})
    # Short names too ambiguous to auto-link.
    ambiguous_short_names = c.ListOfItems(c.Type(str), default=[])
    # When a short name resolves to several anchors, prefer the one under this
    # parent class. Maps short-name → class name.
    prefer_class_for_short = c.Type(dict, default={})
    # Short names never linked from inline code.
    short_name_blocklist = c.ListOfItems(c.Type(str), default=[])
    # Extra lowercase short names to treat as linkable (registry-export keys are
    # included automatically).
    extra_short_names = c.ListOfItems(c.Type(str), default=[])
    # Additional submodules whose ``__all__`` should be indexed (dotted paths).
    extra_modules = c.ListOfItems(c.Type(str), default=[])
    # mkdocstrings category-section anchor suffixes (not primary symbols).
    section_suffixes = c.ListOfItems(c.Type(str), default=["-functions", "-attributes", "-classes"])
    linkify = c.SubConfig(LinkifyConfig)


class SymbolsConfig(base.Config):
    """Relabel and recolor the API symbol-kind badges (headings + TOC).

    ``labels`` maps a kind to the text shown in its badge ("" hides it);
    ``colors`` maps a kind to ``{fg: ..., bg: ...}`` (any CSS color). Both are
    override-only — unset kinds keep the bundled defaults. Recognized kinds:
    ``module``, ``class``, ``dataclass``, ``enum``, ``function``, ``method``,
    ``attribute``, ``type_alias``, ``member``, ``property``.
    """

    labels = c.Type(dict, default={})
    colors = c.Type(dict, default={})
    # Relabel the *text* of mkdocstrings decorator labels (rendered by griffe),
    # e.g. ``{property: "prop", classmethod: "cls", dataclass: "data"}``. ``""``
    # removes the label. Applied to both headings and the TOC at build time.
    decorator_labels = c.Type(dict, default={})


class HighlightConfig(base.Config):
    """Shiki syntax highlighting."""

    # Bundled theme id (``shades-of-purple``) or a path to a Shiki theme JSON.
    # Falls back to ``theme.shiki_theme`` when unset.
    theme = c.Optional(c.Type(str))
    # Highlight inline code spans too (not just fenced blocks).
    inline = c.Type(bool, default=True)
    # Language assumed for fenced blocks with no explicit language.
    default_language = c.Type(str, default="python")
    # Grammars to preload.
    languages = c.ListOfItems(c.Type(str), default=_DEFAULT_LANGUAGES)
    # Language aliases (``py`` → ``python``).
    aliases = c.Type(dict, default=_DEFAULT_LANG_ALIASES)


class PyodideConfig(base.Config):
    """In-browser (WebAssembly) Python runtime for live code on static sites."""

    # Pyodide version + CDN. ``index_url`` overrides the derived jsdelivr URL.
    version = c.Type(str, default="0.27.2")
    index_url = c.Optional(c.Type(str))
    # Packages to install (via micropip) before running — only those with
    # WASM wheels work (e.g. numpy, pandas; not torch/mujoco).
    packages = c.ListOfItems(c.Type(str), default=[])


class LiveCodeConfig(base.Config):
    """Runnable code blocks.

    ``runtime``: ``jupyter`` (local kernel), ``pyodide`` (in-browser WASM, works
    on a published static site), or ``auto`` (Jupyter if reachable, else Pyodide).
    """

    enabled = c.Type(bool, default=True)
    runtime = c.Choice(("auto", "jupyter", "pyodide"), default="auto")
    pyodide = c.SubConfig(PyodideConfig)
    jupyter_url = c.Type(str, default="http://127.0.0.1:8888/")
    # Auth token. Defaults to ``<package>-docs``.
    token = c.Optional(c.Type(str))
    # Dev-only helper port that ``mkdocs serve`` exposes so the header switch can
    # spawn Jupyter without restarting the build.
    launcher_port = c.Type(int, default=8889)
    # Path (relative to the mkdocs.yml dir) to a script that starts Jupyter.
    launcher_script = c.Optional(c.Type(str))
    kernel = c.Type(str, default="python3")
    runnable_languages = c.ListOfItems(c.Type(str), default=["python", "bash"])
    connect_timeout_ms = c.Type(int, default=25000)
    execute_timeout_ms = c.Type(int, default=90000)


class ThemeConfig(base.Config):
    """Shades-of-Purple palette, layout, and Shiki highlighting."""

    # Deprecated alias for ``theme.highlight.theme`` (kept for convenience).
    shiki_theme = c.Type(str, default="shades-of-purple")
    # Override any ``--rd-*`` palette token, e.g. ``page_bg: "#1e1e3f"``.
    palette = c.Type(dict, default={})
    # Override layout tokens, e.g. ``content_max_width: "61rem"``.
    layout = c.Type(dict, default={})
    highlight = c.SubConfig(HighlightConfig)


class TocConfig(base.Config):
    """In-page table-of-contents behavior."""

    # Collapse nested API symbol/category sections by default (expand on click).
    collapse_default = c.Type(bool, default=True)
    # Extra px subtracted when scroll-spy decides the active heading (tune for
    # tall sticky headers). 0 = engine default.
    scrollspy_offset = c.Type(int, default=0)


class FeaturesConfig(base.Config):
    """Coarse on/off toggles for each piece of the experience."""

    shiki = c.Type(bool, default=True)
    api_hover = c.Type(bool, default=True)  # code-block symbol hover/click
    linkify_inline_code = c.Type(bool, default=True)  # inline `Symbol` → API link
    toc_collapsible = c.Type(bool, default=True)
    toc_scrollspy = c.Type(bool, default=True)
    hide_empty_toc = c.Type(bool, default=True)


class RichDocsConfig(base.Config):
    """Top-level config for the ``richdocs`` plugin."""

    # The Python package to document, index, and auto-link. Required.
    package = c.Type(str, default="")
    api = c.SubConfig(ApiConfig)
    symbols = c.SubConfig(SymbolsConfig)
    live_code = c.SubConfig(LiveCodeConfig)
    theme = c.SubConfig(ThemeConfig)
    toc = c.SubConfig(TocConfig)
    features = c.SubConfig(FeaturesConfig)
