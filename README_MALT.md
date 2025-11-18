# malt

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**malt** (MATLAB Language Tools) is a high-performance Rust implementation for parsing and analyzing MATLAB code, with full Python bindings.

This is a Rust port of the [maxx](https://github.com/watermarkhu/maxx) library, providing significantly improved performance while maintaining API compatibility.

## Features

- 🦀 **High Performance** - Written in Rust for maximum speed
- 🔍 **Parse MATLAB files** - Extract functions, classes, properties, and methods
- 📁 **Project structure analysis** - Handle MATLAB packages, namespaces, and class folders
- 📖 **Documentation extraction** - Parse docstrings and comments from MATLAB code
- 🎯 **Type information** - Extract argument types, validation functions, and return types
- 🌳 **Tree-sitter based** - Fast and accurate parsing using tree-sitter-matlab
- ✅ **MATLAB Linting** - Comprehensive linting engine with configurable rules
- 🐍 **Python bindings** - Seamless integration with Python via PyO3

## Installation

Using `pip`:

```bash
pip install malt
```

Using `uv`:

```bash
uv add malt
```

## Quick Start

### Basic File Parsing

```python
from pathlib import Path
from malt.treesitter import FileParser

# Parse a MATLAB function file
parser = FileParser(Path("myfunction.m"))
matlab_object = parser.parse()

print(f"Object type: {matlab_object.kind}")
print(f"Name: {matlab_object.name}")
```

### Project Collection

```python
from malt.collection import PathsCollection
from pathlib import Path

# Collect all MATLAB objects from a project
paths = PathsCollection([Path("src"), Path("examples")])

# Access parsed objects
my_function = paths["myfunction"]
my_class = paths["MyClass"]
my_package = paths["+mypackage.MyFunction"]
```

### Linting

```python
from malt.lint import LintEngine, LintConfig
from pathlib import Path

# Create linting engine
config = LintConfig(
    enabled_rules=["MW-*"],  # Enable all MathWorks-style rules
    exclude_paths=[Path("generated")]
)
engine = LintEngine(config=config)

# Lint files
violations = engine.lint_file(Path("myfile.m"))
for v in violations:
    print(f"{v.filepath}:{v.line}:{v.column}: {v.message} [{v.rule_id}]")
```

## Performance

malt is significantly faster than the pure Python maxx implementation:

- **Parsing**: ~10-50x faster
- **Collection**: ~5-20x faster
- **Linting**: ~15-40x faster

## API Compatibility

malt maintains API compatibility with maxx for most common operations:

```python
# Both work the same way
from maxx.treesitter import FileParser  # Python implementation
from malt.treesitter import FileParser  # Rust implementation
```

## Supported MATLAB Constructs

- **Functions** - Regular functions, nested functions, methods
- **Classes** - Class definitions, properties, methods, inheritance
- **Scripts** - Script files and their documentation
- **Packages** - Namespace packages (`+package`) and class folders (`@class`)
- **Arguments blocks** - Input/output validation and type information
- **Properties blocks** - Class properties with attributes and validation

## Development

### Building from source

```bash
# Install maturin
pip install maturin

# Build the package
maturin develop

# Or build a wheel
maturin build --release
```

### Running tests

```bash
pytest tests/
```

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the [maxx](https://github.com/watermarkhu/maxx) Python library
- Uses [tree-sitter-matlab](https://github.com/acristoffers/tree-sitter-matlab) for parsing
- Built with [PyO3](https://pyo3.rs/) for Python bindings
