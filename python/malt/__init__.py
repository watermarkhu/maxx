"""MALT (MATLAB Language Tools) - Rust-powered MATLAB parsing and analysis.

This module provides Python bindings to the high-performance Rust implementation
of MATLAB parsing and analysis tools.

Example:
    >>> from malt.treesitter import FileParser
    >>> from pathlib import Path
    >>> parser = FileParser(Path("myfile.m"))
    >>> obj = parser.parse()
    >>> print(obj.name)
"""

# Import the Rust extension module
from malt.malt import *  # noqa: F401, F403

# Re-export commonly used items for convenience
from malt.malt import (
    # Enums
    Kind,
    ArgumentKind,
    AccessKind,
    # Objects
    Object,
    Function,
    Class,
    Property,
    Script,
    Namespace,
    Folder,
    # Tree-sitter
    FileParser,
    parse_file,
    # Collection
    PathsCollection,
    # Linting
    LintEngine,
    LintConfig,
    Rule,
    Violation,
    # Exceptions
    MaltError,
    CyclicAliasError,
    FilePathError,
    NameResolutionError,
)

__version__ = "0.6.0"
__all__ = [
    # Enums
    "Kind",
    "ArgumentKind",
    "AccessKind",
    # Objects
    "Object",
    "Function",
    "Class",
    "Property",
    "Script",
    "Namespace",
    "Folder",
    # Tree-sitter
    "FileParser",
    "parse_file",
    # Collection
    "PathsCollection",
    # Linting
    "LintEngine",
    "LintConfig",
    "Rule",
    "Violation",
    # Exceptions
    "MaltError",
    "CyclicAliasError",
    "FilePathError",
    "NameResolutionError",
]
