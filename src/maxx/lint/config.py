"""Configuration system for MATLAB linting."""

from __future__ import annotations

import fnmatch
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class LintConfig:
    """Configuration for MATLAB linting.

    Attributes:
        enabled: Whether linting is enabled globally
        select: List of rule patterns to select (e.g., ["W*", "E001"])
        ignore: List of rule IDs to ignore
        exclude: List of file/directory patterns to exclude
        rule_config: Per-rule configuration overrides
    """

    enabled: bool = True
    select: list[str] = field(default_factory=lambda: ["*"])
    ignore: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    rule_config: dict[str, dict[str, object]] = field(default_factory=dict)

    @classmethod
    def from_toml(cls, filepath: Path) -> LintConfig:
        """Load configuration from a TOML file.

        Args:
            filepath: Path to the matlab.toml file

        Returns:
            LintConfig instance
        """
        if not filepath.exists():
            return cls()

        with open(filepath, "rb") as f:
            data = tomllib.load(f)

        if "lint" not in data:
            return cls()

        lint_data = data["lint"]

        # Extract rule-specific config
        rule_config = {}
        if "rules" in lint_data:
            rule_config = lint_data.pop("rules")

        return cls(
            enabled=lint_data.get("enabled", True),
            select=lint_data.get("select", ["*"]),
            ignore=lint_data.get("ignore", []),
            exclude=lint_data.get("exclude", []),
            rule_config=rule_config,
        )

    @classmethod
    def find_config(cls, start_path: Path | None = None) -> LintConfig:
        """Find and load configuration file.

        Searches for matlab.toml in the current directory and parent directories.

        Args:
            start_path: Starting directory for search (defaults to current directory)

        Returns:
            LintConfig instance
        """
        if start_path is None:
            start_path = Path.cwd()

        # Search up the directory tree for matlab.toml
        current = start_path.resolve()
        while True:
            config_path = current / "matlab.toml"
            if config_path.exists():
                return cls.from_toml(config_path)

            parent = current.parent
            if parent == current:
                # Reached root directory
                break
            current = parent

        # No config file found, return default
        return cls()

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled based on configuration.

        Args:
            rule_id: Rule identifier

        Returns:
            True if the rule should be enabled
        """
        if not self.enabled:
            return False

        # Check if rule is explicitly ignored
        if rule_id in self.ignore:
            return False

        # Check if rule matches any select pattern
        for pattern in self.select:
            if fnmatch.fnmatch(rule_id, pattern):
                return True

        return False

    def is_path_excluded(self, filepath: Path, base_path: Path | None = None) -> bool:
        """Check if a path should be excluded from linting.

        Args:
            filepath: Path to check
            base_path: Base path for relative exclusion patterns

        Returns:
            True if the path should be excluded
        """
        if base_path is not None:
            try:
                relative_path = filepath.relative_to(base_path)
            except ValueError:
                relative_path = filepath
        else:
            relative_path = filepath

        path_str = str(relative_path)

        for pattern in self.exclude:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Also check if any parent directory matches
            for parent in relative_path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True

        return False

    def get_rule_config(self, rule_id: str) -> dict[str, object]:
        """Get configuration overrides for a specific rule.

        Args:
            rule_id: Rule identifier

        Returns:
            Dictionary of configuration overrides
        """
        return self.rule_config.get(rule_id, {})
