"""Linting functionality for MATLAB code analysis.

This module provides a plugin-based linting system similar to ruff,
allowing users to define rules via TOML files and run linting on MATLAB codebases.
"""

from __future__ import annotations

from maxx.lint.config import LintConfig
from maxx.lint.engine import LintEngine
from maxx.lint.rule import Rule
from maxx.lint.violation import Violation

__all__ = [
    "LintConfig",
    "LintEngine",
    "Rule",
    "Violation",
]
