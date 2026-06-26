"""Tests for the config schema defaults and generated assets."""

from __future__ import annotations

import json
import types

from richdocs import _assets
from richdocs._config import RichDocsConfig


def _validated(d: dict) -> RichDocsConfig:
    cfg = RichDocsConfig()
    cfg.load_dict(d)
    errors, _warnings = cfg.validate()
    assert not errors, errors
    return cfg


def test_only_package_required_defaults_populated():
    cfg = _validated({"package": "mypkg"})
    assert cfg.package == "mypkg"
    assert cfg.api.id_prefix is None  # resolved to package by the plugin
    assert cfg.live_code.enabled is True
    assert cfg.live_code.launcher_port == 8889
    assert cfg.theme.shiki_theme == "shades-of-purple"
    assert cfg.features.api_hover is True
    assert cfg.api.section_suffixes == ["-functions", "-attributes", "-classes"]


def test_theme_overrides_css_friendly_and_raw_keys():
    theme = types.SimpleNamespace(
        palette={"page_bg": "#101010", "--rd-gold": "#ffcc00", "unknownKey": "x"},
        layout={"toc_row_gap": "0.5rem"},
    )
    css = _assets.generate_theme_overrides_css(types.SimpleNamespace(theme=theme))
    assert "--rd-page-bg: #101010;" in css  # friendly -> token
    assert "--rd-gold: #ffcc00;" in css  # raw token passthrough
    assert "--rd-toc-row-gap: 0.5rem;" in css  # layout key
    assert "unknownKey" not in css  # ignored with a warning
    assert css.strip().startswith('[data-md-color-scheme="slate"]')


def test_theme_overrides_css_empty():
    empty = types.SimpleNamespace(theme=types.SimpleNamespace(palette={}, layout={}))
    assert "no theme overrides" in _assets.generate_theme_overrides_css(empty)


def test_generated_config_js_shape():
    cfg = _validated({"package": "mypkg", "live_code": {"token": "tok", "launcher_port": 9000}})
    js = _assets.generate_config_js(cfg, id_prefix="mypkg", token="tok", assets_dir=_assets_dir())
    assert js.startswith("window.__richdocsConfig = ")
    payload = json.loads(js.split("= ", 1)[1].rstrip().rstrip(";"))
    assert payload["api"]["idPrefix"] == "mypkg"
    assert payload["jupyter"]["token"] == "tok"
    assert payload["jupyter"]["launcherPort"] == 9000
    assert payload["jupyter"]["launcherPath"] == "/__richdocs/jupyter"
    assert payload["theme"]["shikiThemeName"] == "Shades of Purple"


def _assets_dir():
    from richdocs.plugin import ASSETS_DIR

    return ASSETS_DIR
