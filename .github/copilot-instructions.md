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

