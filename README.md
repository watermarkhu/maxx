# maxx

[![CI](https://github.com/watermarkhu/maxx/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/watermarkhu/maxx/actions/workflows/ci.yml)
[![pypi version](https://img.shields.io/pypi/v/maxx.svg)](https://pypi.org/project/maxx/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<img src="https://raw.githubusercontent.com/watermarkhu/maxx/refs/heads/main/img/malt-pixel.svg" alt="malt logo, created by Mark Shui Hu" width="100" align="right">

**maxx** (MATLAB Language Tools) is a Python library for parsing and analyzing MATLAB code. It provides comprehensive support for extracting signatures, documentation, and metadata from MATLAB projects including functions, classes, scripts, and packages.

### Features

- 🔍 **Parse MATLAB files** - Extract functions, classes, properties, and methods
- 📁 **Project structure analysis** - Handle MATLAB packages, namespaces, and class folders
- 📖 **Documentation extraction** - Parse docstrings and comments from MATLAB code
- 🎯 **Type information** - Extract argument types, validation functions, and return types
- 🌳 **Tree-sitter based** - Fast and accurate parsing using tree-sitter-matlab
- 🔗 **Integration ready** - Built for documentation generators like MkDocs

## Installation

Using `pip`:

```bash
pip install maxx
```

Using `uv`:

```bash
uv add maxx
```

## Quick Start

### Basic File Parsing

```python
from pathlib import Path
from maxx.treesitter import FileParser

# Parse a MATLAB function file
parser = FileParser(Path("myfunction.m"))
matlab_object = parser.parse()

print(f"Object type: {matlab_object.kind}")
print(f"Name: {matlab_object.name}")
print(f"Arguments: {matlab_object.arguments}")
print(f"Docstring: {matlab_object.docstring}")
```

### Project Collection

```python
from maxx.collection import PathsCollection
from pathlib import Path

# Collect all MATLAB objects from a project
paths = PathsCollection([Path("src"), Path("examples")])

# Access parsed objects
my_function = paths["myfunction"]
my_class = paths["MyClass"]
my_package = paths["+mypackage.MyFunction"]
```

### Working with Classes

```python
# Access class members
matlab_class = paths["MyClass"]
print(f"Base classes: {matlab_class.bases}")
print(f"Properties: {list(matlab_class.members.keys())}")

# Access methods and properties
constructor = matlab_class.constructor
properties = [m for m in matlab_class.members.values() if m.is_property]
```

## Supported MATLAB Constructs

- **Functions** - Regular functions, nested functions, methods
- **Classes** - Class definitions, properties, methods, inheritance
- **Scripts** - Script files and their documentation
- **Packages** - Namespace packages (`+package`) and class folders (`@class`)
- **Arguments blocks** - Input/output validation and type information
- **Properties blocks** - Class properties with attributes and validation


## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
