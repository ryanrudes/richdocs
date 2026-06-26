"""Tests for the v0.2 configurability: symbols, linkify, highlight, toc."""

from __future__ import annotations

import json

from richdocs import _assets
from richdocs._config import RichDocsConfig
from richdocs._linkify import Linkifier
from richdocs.plugin import ASSETS_DIR


def _cfg(extra: dict) -> RichDocsConfig:
    cfg = RichDocsConfig()
    cfg.load_dict({"package": "demo", **extra})
    errors, _ = cfg.validate()
    assert not errors, errors
    return cfg


def test_symbols_css_labels_and_colors():
    css = _assets.generate_symbols_css(
        _cfg(
            {
                "symbols": {
                    "labels": {"class": "klass", "function": "fn"},
                    "colors": {"enum": {"fg": "#0f0", "bg": "#001"}, "method": {"fg": "#f0f"}},
                }
            }
        )
    )
    assert "code.doc-symbol-class::after" in css
    assert 'content: "klass" !important' in css
    assert 'content: "fn" !important' in css
    assert "--doc-symbol-enum-fg-color: #0f0;" in css
    assert "--doc-symbol-enum-bg-color: #001;" in css
    # color also emits a direct rule (covers contexts the vars miss)
    assert "code.doc-symbol-method" in css and "color: #f0f !important" in css


def test_symbols_css_empty_by_default():
    assert "no symbol" in _assets.generate_symbols_css(_cfg({})).lower()


def test_config_js_exposes_linkify_highlight_toc():
    cfg = _cfg(
        {
            "api": {"linkify": {"short_names": False, "dotted": False, "aliases": {"X": "demo.X"}}},
            "theme": {"highlight": {"languages": ["rust"], "inline": False, "default_language": "rust"}},
            "toc": {"collapse_default": False, "scrollspy_offset": 40},
        }
    )
    js = _assets.generate_config_js(cfg, id_prefix="demo", token="t", assets_dir=ASSETS_DIR)
    payload = json.loads(js.split("= ", 1)[1].rstrip().rstrip(";"))
    assert payload["api"]["linkify"] == {
        "shortNames": False,
        "dotted": False,
        "codeBlocks": True,
        "aliases": {"X": "demo.X"},
    }
    assert payload["theme"]["highlight"]["languages"] == ["rust"]
    assert payload["theme"]["highlight"]["inline"] is False
    assert payload["theme"]["highlight"]["defaultLanguage"] == "rust"
    assert payload["toc"] == {"collapseDefault": False, "scrollspyOffset": 40}


def test_highlight_theme_alias_fallback():
    # theme.highlight.theme wins; else falls back to theme.shiki_theme.
    assert _assets.effective_shiki_theme(_cfg({"theme": {"shiki_theme": "x"}})) == "x"
    assert _assets.effective_shiki_theme(_cfg({"theme": {"shiki_theme": "x", "highlight": {"theme": "y"}}})) == "y"


class _FakeIndex:
    def build_autoref_index(self):
        return ({"demo.Robot": "demo.Robot"}, {"Robot": "demo.Robot"})

    def resolve_identifier(self, text, by_id, by_short, *, short_names=True, dotted=True):
        if text in by_id:
            return text
        if short_names and text in by_short:
            return by_short[text]
        return None


def test_linkify_short_names_toggle():
    linked = Linkifier(_FakeIndex(), link_short_names=True).linkify_markdown("`Robot`")
    assert linked == "[`Robot`][demo.Robot]"
    off = Linkifier(_FakeIndex(), link_short_names=False).linkify_markdown("`Robot`")
    assert off == "`Robot`"


def test_linkify_aliases_and_skip_extensions():
    lk = Linkifier(_FakeIndex(), aliases={"the bot": "demo.Robot"}, skip_extensions=["rst"])
    assert "[`the bot`][demo.Robot]" in lk.linkify_markdown("Use `the bot`.")
    assert lk.linkify_markdown("`notes.rst`") == "`notes.rst`"
