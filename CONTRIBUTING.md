# Contributing

Thanks for your interest in improving **richdocs**!

## Development setup

```bash
git clone https://github.com/ryanrudes/richdocs
cd richdocs
uv venv
uv pip install -e ".[dev]"
```

## Checks

Please make sure these pass before opening a PR (CI runs the same):

```bash
uv run ruff check .        # lint
uv run ruff format --check .
uv run mypy                # type-check
uv run pytest              # unit tests
uv build                   # packaging (bundles the front-end assets)
```

The front-end assets (`src/richdocs/assets/**`) are plain `.mjs` / `.css` /
`.jinja` — after editing them, a quick `node --check <file>.mjs` catches syntax
errors, and `mkdocs serve` in a demo project is the best way to verify behavior.

## Conventions

- Python is formatted/linted with **ruff** (line length 120) and type-checked
  with **mypy**.
- Keep the config surface small and well-documented — every option lives in
  `src/richdocs/_config.py` and should have a sensible default.
- Internal CSS/JS identifiers use the `rd-` / `--rd-` prefix; the bundled theme
  is referred to by its full name, "Shades of Purple".

## Releasing

Releases are published to PyPI by the `release` workflow when a GitHub Release is
created (via PyPI Trusted Publishing). Bump the version in
`pyproject.toml`, update `CHANGELOG.md`, tag `vX.Y.Z`, and publish the release.
