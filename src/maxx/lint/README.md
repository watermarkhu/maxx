# MATLAB Linting System

A plugin-based linting system for MATLAB code, similar to `ruff` for Python.

## Features

- **Tree-sitter based**: Uses tree-sitter-matlab for accurate, fast parsing
- **Plugin system**: Define custom rules via TOML files
- **Configurable**: Use `matlab.toml` to enable/disable rules
- **CLI interface**: Run linting from the command line
- **PathsCollection integration**: Automatically finds MATLAB files

## Quick Start

### Run linting on your project

```bash
# Lint current directory
maxx lint

# Lint specific paths
maxx lint src/ tests/

# Lint with custom config
maxx lint --config my-matlab.toml

# Exit with error if violations found (for CI)
maxx lint --check
```

### List available rules

```bash
# Show enabled rules
maxx rules

# Show all rules (including disabled)
maxx rules --all
```

## Configuration

Create a `matlab.toml` file in your project root:

```toml
[lint]
enabled = true
select = ["*"]      # Enable all rules
ignore = ["W001"]   # Ignore specific rules
exclude = ["tests/*", "build/*"]

# Per-rule configuration
[lint.rules.W002]
max-line-length = 120
```

### Configuration Options

- `enabled`: Enable/disable linting globally (default: true)
- `select`: List of rule patterns to enable (default: ["*"])
- `ignore`: List of rule IDs to ignore (default: [])
- `exclude`: List of file/directory patterns to exclude (default: [])
- `rules.<rule-id>`: Per-rule configuration overrides

### Rule Selection Patterns

- `["*"]` - All rules
- `["W*"]` - All warnings
- `["E*"]` - All errors
- `["W001", "E001"]` - Specific rules

## Built-in Rules

| ID | Name | Severity | Description |
|----|------|----------|-------------|
| W001 | missing-docstring | warning | Function definition is missing a docstring |
| W002 | prefer-end-keyword | info | Block should use 'end' keyword for clarity |
| W003 | global-variable | warning | Use of global variables detected |
| W004 | eval-usage | warning | Use of eval() is discouraged |
| E001 | syntax-error | error | Syntax error detected by parser |

## Creating Custom Rules

Rules are defined as TOML files in the `rules/` directory. Each rule specifies a tree-sitter query pattern.

### Rule Format

```toml
[rule]
id = "W001"
name = "my-custom-rule"
description = "Description of what this rule checks"
severity = "warning"  # "error", "warning", or "info"
enabled = true

[query]
# Tree-sitter query pattern
pattern = """
(function_definition
  name: (identifier) @function_name
) @function
"""

[message]
# Message template with variable substitution
template = "Function '{function_name}' violates rule at line {line}"
```

### Query Variables

The following variables are available in message templates:

- `{line}` - Line number
- `{column}` - Column number
- `{name}` - Text of the first captured node
- `{<capture_name>}` - Text of any named capture from the query

### Tree-sitter Query Syntax

Learn more about tree-sitter queries:
- [Tree-sitter Query Syntax](https://tree-sitter.github.io/tree-sitter/using-parsers#query-syntax)
- [MATLAB Grammar](https://github.com/acristoffers/tree-sitter-matlab)

Use `maxx` with tree-sitter queries to explore the AST of your MATLAB files.

## CLI Reference

### `maxx lint`

Lint MATLAB files.

```bash
maxx lint [PATHS...] [OPTIONS]
```

**Arguments:**
- `PATHS` - Files or directories to lint (default: current directory)

**Options:**
- `--config PATH` - Path to matlab.toml configuration file
- `--no-recursive` - Don't recursively search directories
- `-v, --verbose` - Show verbose output including node text
- `--check` - Exit with error code if violations are found
- `--select RULES` - Comma-separated list of rule patterns to select
- `--ignore RULES` - Comma-separated list of rule IDs to ignore

**Examples:**

```bash
# Lint current directory
maxx lint

# Lint specific files
maxx lint src/myfile.m

# Lint with specific rules
maxx lint --select "W*,E001"

# Ignore specific rules
maxx lint --ignore "W001,W002"

# Use in CI/CD
maxx lint --check
```

### `maxx rules`

List available linting rules.

```bash
maxx rules [OPTIONS]
```

**Options:**
- `--all` - Show all rules including disabled ones

## Integration

### With CI/CD

```yaml
# GitHub Actions example
- name: Lint MATLAB code
  run: |
    uv run maxx lint --check
```

### With Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: maxx-lint
      name: MATLAB Linting
      entry: uv run maxx lint --check
      language: system
      types: [file]
      files: \.m$
```

## Development

### Adding New Rules

1. Create a new TOML file in `src/maxx/rules/`
2. Define the rule following the format above
3. Test with `maxx lint`

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run ty check
```

### Linting (Python)

```bash
uv run ruff check
uv run ruff format
```
