"""Tests for v0.3: decorator-label relabeling + Pyodide runtime config."""

from __future__ import annotations

import json

from richdocs import _assets
from richdocs._config import RichDocsConfig
from richdocs._toc_labels import relabel_decorator_labels
from richdocs.plugin import ASSETS_DIR


def _cfg(extra: dict) -> RichDocsConfig:
    cfg = RichDocsConfig()
    cfg.load_dict({"package": "demo", **extra})
    errors, _ = cfg.validate()
    assert not errors, errors
    return cfg


def test_decorator_relabel_rewrites_text_and_avoids_substrings(tmp_path):
    page = tmp_path / "api" / "x"
    page.mkdir(parents=True)
    (page / "index.html").write_text(
        '<small class="doc doc-label doc-label-property"><code>property</code></small>'
        '<small class="doc doc-label doc-label-toc doc-label-classmethod"><code>classmethod</code></small>'
        '<small class="doc doc-label doc-label-class-attribute"><code>class-attribute</code></small>',
        encoding="utf-8",
    )
    relabel_decorator_labels(tmp_path, {"property": "prop", "classmethod": "cls", "class": "CLASS"})
    out = (page / "index.html").read_text()
    assert "<code>prop</code>" in out  # heading label rewritten
    assert "<code>cls</code>" in out  # TOC label rewritten
    # `class` must NOT match the longer `doc-label-class-attribute`
    assert "<code>class-attribute</code>" in out


def test_decorator_relabel_no_op_when_unconfigured(tmp_path):
    page = tmp_path / "api"
    page.mkdir(parents=True)
    html = '<small class="doc doc-label doc-label-property"><code>property</code></small>'
    (page / "index.html").write_text(html, encoding="utf-8")
    relabel_decorator_labels(tmp_path, {})
    assert (page / "index.html").read_text() == html


def test_runtime_and_pyodide_config_emitted():
    cfg = _cfg(
        {
            "live_code": {
                "runtime": "pyodide",
                "pyodide": {"version": "0.27.0", "packages": ["numpy", "rich"]},
            }
        }
    )
    js = _assets.generate_config_js(cfg, id_prefix="demo", token="t", assets_dir=ASSETS_DIR)
    payload = json.loads(js.split("= ", 1)[1].rstrip().rstrip(";"))
    assert payload["jupyter"]["runtime"] == "pyodide"
    assert payload["jupyter"]["pyodide"]["version"] == "0.27.0"
    assert payload["jupyter"]["pyodide"]["packages"] == ["numpy", "rich"]


def test_runtime_defaults_to_auto():
    cfg = _cfg({})
    js = _assets.generate_config_js(cfg, id_prefix="demo", token="t", assets_dir=ASSETS_DIR)
    payload = json.loads(js.split("= ", 1)[1].rstrip().rstrip(";"))
    assert payload["jupyter"]["runtime"] == "auto"
    assert payload["jupyter"]["pyodide"]["packages"] == []


def test_invalid_runtime_rejected():
    cfg = RichDocsConfig()
    cfg.load_dict({"package": "demo", "live_code": {"runtime": "nope"}})
    errors, _ = cfg.validate()
    assert errors  # Choice() rejects unknown runtime values
