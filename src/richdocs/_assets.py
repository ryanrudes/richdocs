"""Register the plugin's bundled front-end assets with the MkDocs build.

A downstream project lists a single ``plugins: [richdocs]`` entry; this module wires
the bundled stylesheets/scripts into ``extra_css`` / ``extra_javascript``, copies
the static asset tree into the site, points mkdocstrings at the bundled
templates, and generates the runtime config object the JS modules read.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mkdocs.structure.files import File

from richdocs._jupyter import LAUNCHER_PREFIX

if TYPE_CHECKING:
    from richdocs._config import RichDocsConfig

log = logging.getLogger("mkdocs.plugins.richdocs")

#: Subdirectories under assets/ copied verbatim into the built site.
_STATIC_SUBDIRS = ("javascripts", "stylesheets", "themes")
#: Generated runtime config consumed by the JS modules.
CONFIG_JS_URI = "javascripts/richdocs-config.js"
#: Generated palette/layout overrides, loaded after the static stylesheets.
PALETTE_CSS_URI = "stylesheets/richdocs-palette.css"

#: Friendly ``theme.palette`` / ``theme.layout`` keys → the CSS custom property
#: they set. Any key beginning with ``--`` is passed through verbatim, so power
#: users can override any token even if it has no friendly alias.
_THEME_KEYS = {
    # palette (colors)
    "page_bg": "--rd-page-bg",
    "sidebar_bg": "--rd-sidebar-bg",
    "code_bg": "--rd-editor-bg",
    "editor_bg": "--rd-editor-bg",
    "code_fg": "--rd-code-fg",
    "surface_1": "--rd-surface-1",
    "surface_2": "--rd-surface-2",
    "surface_3": "--rd-surface-3",
    "surface_4": "--rd-surface-4",
    "text": "--rd-text",
    "text_muted": "--rd-text-muted",
    "text_soft": "--rd-text-soft",
    "purple": "--rd-purple",
    "purple_bright": "--rd-purple-bright",
    "gold": "--rd-gold",
    "accent": "--rd-gold",
    "enum_fg": "--doc-symbol-enum-fg-color",
    "enum_bg": "--doc-symbol-enum-bg-color",
    "member_fg": "--doc-symbol-member-fg-color",
    "member_bg": "--doc-symbol-member-bg-color",
    # layout (spacing)
    "toc_row_gap": "--rd-toc-row-gap",
    "toc_branch_gap": "--rd-toc-branch-gap",
    "toc_section_gap": "--rd-toc-section-gap",
    "toc_link_min_height": "--rd-toc-link-min-height",
}


def bundled_static_files(assets_dir: Path, config: Any) -> list[File]:
    """`File` objects copying the bundled JS/CSS/theme tree into the site root."""
    files: list[File] = []
    use_dir_urls = bool(config.get("use_directory_urls", True))
    for sub in _STATIC_SUBDIRS:
        base = assets_dir / sub
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(assets_dir).as_posix()
            files.append(File(rel, str(assets_dir), config["site_dir"], use_dir_urls))
    return files


def register_static_assets(config: Any, richdocs_config: RichDocsConfig) -> None:
    """Prepend the plugin's CSS/JS (gated by feature toggles) to the config."""
    feat = richdocs_config.features
    live = richdocs_config.live_code

    # richdocs-palette.css (generated) loads last so palette/layout overrides win;
    # any project extra_css after that still overrides the plugin.
    css = ["stylesheets/theme.css", "stylesheets/extra.css", PALETTE_CSS_URI]
    config["extra_css"] = css + list(config.get("extra_css") or [])

    loaders = [CONFIG_JS_URI]
    if feat.hide_empty_toc:
        loaders.append("javascripts/hide-empty-toc.js")
    if feat.toc_collapsible:
        loaders.append("javascripts/toc-collapsible-loader.js")
    if feat.toc_scrollspy:
        loaders.append("javascripts/toc-scrollspy.js")
    if feat.shiki:
        loaders.append("javascripts/shiki-loader.js")
    if live.enabled:
        loaders.append("javascripts/live-code-loader.js")
    if feat.api_hover:
        loaders.append("javascripts/api-navigation-loader.js")
    # Runtime TOC-label sync complements the post-build pass; harmless otherwise.
    loaders.append("javascripts/sync-toc-labels-loader.js")

    config["extra_javascript"] = loaders + list(config.get("extra_javascript") or [])


def resolve_shiki_theme_name(shiki_theme: str, assets_dir: Path) -> str:
    """Read the Shiki theme JSON's registered ``name`` (matches codeToHtml's theme)."""
    if "/" in shiki_theme or shiki_theme.endswith(".json"):
        candidate = Path(shiki_theme)
    else:
        candidate = assets_dir / "themes" / f"{shiki_theme}-shiki.json"
    try:
        return str(json.loads(candidate.read_text(encoding="utf-8"))["name"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        log.warning("richdocs: could not read theme name from %s; defaulting.", candidate)
        return "Shades of Purple"


def generate_config_js(richdocs_config: RichDocsConfig, *, id_prefix: str, token: str, assets_dir: Path) -> str:
    """Build the ``window.__richdocsConfig`` object the JS modules read at runtime."""
    live = richdocs_config.live_code
    feat = richdocs_config.features
    theme_name = resolve_shiki_theme_name(richdocs_config.theme.shiki_theme, assets_dir)
    payload = {
        "version": 1,
        "api": {
            "idPrefix": id_prefix,
            "indexUrl": "javascripts/api-symbols.json",
            "hover": bool(feat.api_hover),
        },
        "jupyter": {
            "enabled": bool(live.enabled),
            "baseUrl": live.jupyter_url,
            "token": token,
            "kernelName": live.kernel,
            "launcherPath": LAUNCHER_PREFIX,
            "launcherPort": int(live.launcher_port),
            "connectTimeoutMs": int(live.connect_timeout_ms),
            "executeTimeoutMs": int(live.execute_timeout_ms),
            "runnableLanguages": list(live.runnable_languages),
        },
        "theme": {
            "shikiTheme": richdocs_config.theme.shiki_theme,
            "shikiThemeName": theme_name,
        },
        "features": {
            "tocCollapsible": bool(feat.toc_collapsible),
            "tocScrollspy": bool(feat.toc_scrollspy),
        },
    }
    return "window.__richdocsConfig = " + json.dumps(payload, separators=(",", ":")) + ";\n"


def generate_theme_overrides_css(richdocs_config: RichDocsConfig) -> str:
    """Build ``richdocs-palette.css`` from ``theme.palette`` and ``theme.layout``."""
    theme = richdocs_config.theme
    decls: list[tuple[str, str]] = []
    for source in (theme.palette, theme.layout):
        for key, value in source.items():
            key = str(key)
            if key.startswith("--"):
                decls.append((key, str(value)))
            elif key in _THEME_KEYS:
                decls.append((_THEME_KEYS[key], str(value)))
            else:
                log.warning(
                    "richdocs: unknown theme override key %r (ignored). Known keys: %s "
                    "(or pass a raw token like '--rd-page-bg').",
                    key,
                    ", ".join(sorted(_THEME_KEYS)),
                )
    if not decls:
        return "/* richdocs: no theme overrides configured */\n"
    body = "\n".join(f"  {prop}: {value};" for prop, value in decls)
    # Target the slate scheme (where the base tokens live); loaded last so it wins.
    return f'[data-md-color-scheme="slate"] {{\n{body}\n}}\n'


def set_mkdocstrings_templates(config: Any, assets_dir: Path) -> None:
    """Point mkdocstrings at the bundled enum/badge template overrides."""
    md = config["plugins"].get("mkdocstrings")
    if md is None:
        log.warning("richdocs: mkdocstrings is not enabled; enum/decorator-badge template overrides will not apply.")
        return
    current = md.config.get("custom_templates")
    if current:
        log.warning(
            "richdocs: mkdocstrings.custom_templates is already set (%s); leaving it. "
            "richdocs's enum/badge templates may not apply.",
            current,
        )
        return
    md.config["custom_templates"] = str(assets_dir / "templates")
