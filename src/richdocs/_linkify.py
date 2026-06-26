"""On-page-markdown: auto-link inline ``code`` to mkdocstrings/autorefs targets.

Uses the shared :class:`~richdocs._symbol_index.SymbolIndex` to resolve
identifiers, skipping fenced code blocks and obvious non-symbols. What gets
linked is configurable via ``api.linkify`` (short names, dotted expressions,
skipped file extensions, and custom word→symbol aliases).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from richdocs._symbol_index import SymbolIndex

_FENCED_BLOCK_RE = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)", re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"(?<!\[)(`)([^`\n]+)\1(?!\])")

_DEFAULT_SKIP_EXTENSIONS = ("md", "py", "yaml", "yml", "npz", "json", "toml", "txt")


def _build_skip_re(skip_extensions: Sequence[str]) -> re.Pattern[str]:
    exts = "|".join(re.escape(e.lstrip(".")) for e in skip_extensions) or "(?!)"
    return re.compile(rf"[\s/\\]|\.(?:{exts})\b|^[0-9]+$")


class Linkifier:
    """Linkify inline code spans against a project's API symbol index."""

    def __init__(
        self,
        symbol_index: SymbolIndex,
        *,
        skip_extensions: Sequence[str] = _DEFAULT_SKIP_EXTENSIONS,
        link_short_names: bool = True,
        link_dotted: bool = True,
        aliases: Mapping[str, str] | None = None,
    ) -> None:
        self._symbol_index = symbol_index
        self._skip_re = _build_skip_re(skip_extensions)
        self._link_short_names = link_short_names
        self._link_dotted = link_dotted
        self._aliases = dict(aliases or {})
        self._index: tuple[dict[str, str], dict[str, str]] | None = None

    def _resolved_index(self) -> tuple[dict[str, str], dict[str, str]]:
        if self._index is None:
            self._index = self._symbol_index.build_autoref_index()
        return self._index

    def _linkify_segment(self, segment: str) -> str:
        by_id, by_short = self._resolved_index()

        def repl(match: re.Match[str]) -> str:
            inner = match.group(2)
            # Custom aliases win and bypass the skip heuristics (the user opted in).
            if inner in self._aliases:
                return f"[`{inner}`][{self._aliases[inner]}]"
            if self._skip_re.search(inner):
                return match.group(0)
            target = self._symbol_index.resolve_identifier(
                inner,
                by_id,
                by_short,
                short_names=self._link_short_names,
                dotted=self._link_dotted,
            )
            if not target:
                return match.group(0)
            return f"[`{inner}`][{target}]"

        return _INLINE_CODE_RE.sub(repl, segment)

    def linkify_markdown(self, markdown: str) -> str:
        parts = _FENCED_BLOCK_RE.split(markdown)
        for index, part in enumerate(parts):
            if index % 2 == 1:  # inside a fenced block
                continue
            parts[index] = self._linkify_segment(part)
        return "".join(parts)
