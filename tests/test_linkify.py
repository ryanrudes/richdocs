"""Tests for inline-code auto-linking."""

from __future__ import annotations

from richdocs._linkify import Linkifier


class _FakeIndex:
    """Minimal stand-in for SymbolIndex with a fixed symbol table."""

    def build_autoref_index(self):
        return ({"pkg.Robot": "pkg.Robot"}, {"Robot": "pkg.Robot"})

    def resolve_identifier(self, text, by_id, by_short):
        if text in by_id:
            return text
        return by_short.get(text)


def _linkifier() -> Linkifier:
    return Linkifier(_FakeIndex())


def test_links_known_symbol():
    out = _linkifier().linkify_markdown("Use `Robot` to start.")
    assert "[`Robot`][pkg.Robot]" in out


def test_skips_fenced_code_blocks():
    md = "```python\n`Robot`\n```\n\nThen `Robot`."
    out = _linkifier().linkify_markdown(md)
    assert out.count("[`Robot`][pkg.Robot]") == 1  # only the prose mention
    assert "```python\n`Robot`\n```" in out  # fenced block untouched


def test_skips_paths_numbers_and_filenames():
    lk = _linkifier()
    assert lk.linkify_markdown("`foo/bar`") == "`foo/bar`"
    assert lk.linkify_markdown("`42`") == "`42`"
    assert lk.linkify_markdown("`run_config.toml`") == "`run_config.toml`"


def test_leaves_unknown_symbols_alone():
    assert _linkifier().linkify_markdown("`Unknown`") == "`Unknown`"
