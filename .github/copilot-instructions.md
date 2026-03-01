# Copilot Instructions for maxx

## Environment Setup

Set up the environment with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Common Commands

| Task | Command |
|------|---------|
| Run tests | `uv run pytest` |
| Type check | `uv run ty check` |
| Lint (with auto-fix) | `uv run ruff check --fix` |
| Format | `uv run ruff format` |

Always run all four commands before submitting a PR.

## Project Overview

**maxx** is a Python library that parses MATLAB source files and collects MATLAB objects (functions, classes, scripts, namespaces, live scripts, …) into a searchable collection.  It is used as the parsing backend for MATLAB API documentation generators.

### Key modules

| Module | Purpose |
|--------|---------|
| `src/maxx/objects.py` | Data-model classes (`Function`, `Class`, `Script`, `LiveScript`, …) |
| `src/maxx/enums.py` | Enumerations (`Kind`, `ArgumentKind`, `AccessKind`) |
| `src/maxx/collection.py` | `PathsCollection` – discovers and lazily resolves MATLAB files on a path |
| `src/maxx/treesitter.py` | Tree-sitter–based parser for `.m` files |
| `src/maxx/livescript.py` | Parser for `.mlx` binary and R2025a plain-text live scripts |
| `src/maxx/mixins.py` | Shared mixins (`PathMixin`, `ObjectAliasMixin`) |
| `src/maxx/expressions.py` | Expression wrapper around tree-sitter nodes |

### Adding a new MATLAB object type

1. Add a new `Kind` value in `enums.py`.
2. Add a new class (subclassing `PathMixin` and `Object`) in `objects.py`.
3. Hook parsing into `treesitter.py` (`FileParser.parse`) or add a dedicated
   parser module (see `livescript.py` as a reference).
4. Update `collection.py` to glob/resolve the new file type if it uses a
   non-`.m` extension.
5. Export the new module/class in `__init__.py`.
6. Add test files under `tests/files/` and tests in `tests/`.

### Live Script support

MATLAB live scripts come in two flavours:

- **Binary `.mlx`** – a ZIP archive containing `matlab/document.xml` (Office
  Open XML dialect).  Detected by `PK` magic bytes.
- **Plain-text live code (R2025a)** – a `.m` file with `%%`-delimited sections
  and embedded live-editor markup. Saved via *Save As → MATLAB Live Code File
  (UTF-8) (\*.m)* in the Live Editor.

Parsing is handled by `LiveScriptParser` in `src/maxx/livescript.py`.
Live-script collection is **opt-in** (`parse_live_scripts=True` on
`PathsCollection`); it defaults to `False`.
