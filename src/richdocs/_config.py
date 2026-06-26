"""Typed, validated config schema for the ``richdocs`` plugin.

Only ``package`` is required; everything else has sensible defaults. The nested
``api`` / ``live_code`` / ``theme`` / ``features`` groups keep the surface
discoverable and self-documenting.
"""

from __future__ import annotations

from mkdocs.config import base
from mkdocs.config import config_options as c


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
    # Short names too ambiguous to auto-link (heuristic supplement; the engine
    # already drops names that collide across the index automatically).
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


class LiveCodeConfig(base.Config):
    """Runnable code blocks backed by a local Jupyter kernel (dev only)."""

    enabled = c.Type(bool, default=True)
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
    """Shades-of-Purple palette and Shiki highlighting theme."""

    # ``shades-of-purple`` (bundled) or a path to a Shiki theme JSON.
    shiki_theme = c.Type(str, default="shades-of-purple")
    # Override any ``--rd-*`` palette token, e.g. ``page_bg: "#1e1e3f"``.
    palette = c.Type(dict, default={})
    # Override layout tokens, e.g. ``content_max_width: "61rem"``.
    layout = c.Type(dict, default={})


class FeaturesConfig(base.Config):
    """Toggles for each piece of the experience."""

    shiki = c.Type(bool, default=True)
    api_hover = c.Type(bool, default=True)
    linkify_inline_code = c.Type(bool, default=True)
    toc_collapsible = c.Type(bool, default=True)
    toc_scrollspy = c.Type(bool, default=True)
    hide_empty_toc = c.Type(bool, default=True)


class RichDocsConfig(base.Config):
    """Top-level config for the ``richdocs`` plugin."""

    # The Python package to document, index, and auto-link. Required.
    package = c.Type(str, default="")
    api = c.SubConfig(ApiConfig)
    live_code = c.SubConfig(LiveCodeConfig)
    theme = c.SubConfig(ThemeConfig)
    features = c.SubConfig(FeaturesConfig)
