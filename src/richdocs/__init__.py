"""richdocs: a Shades-of-Purple docs experience for MkDocs Material.

A single MkDocs plugin (`richdocs`) that wires up Shiki syntax highlighting, runnable
live code, API-symbol hover/auto-linking, mkdocstrings template overrides, and
TOC enhancements — all driven by a typed, well-defaulted config schema.
"""

from __future__ import annotations

from richdocs.plugin import RichDocsPlugin

__all__ = ["RichDocsPlugin"]
__version__ = "0.3.0"
