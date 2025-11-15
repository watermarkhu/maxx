"""Core linting engine for MATLAB code analysis."""

from __future__ import annotations

from pathlib import Path

import tree_sitter_matlab as tsmatlab
from tree_sitter import Language, Parser

from maxx.collection import PathsCollection
from maxx.lint.config import LintConfig
from maxx.lint.rule import RuleRegistry
from maxx.lint.violation import Violation
from maxx.logger import logger


class LintEngine:
    """Main linting engine that orchestrates rule checking.

    Attributes:
        registry: Rule registry containing all available rules
        config: Linting configuration
        parser: Tree-sitter parser for MATLAB
    """

    def __init__(
        self,
        registry: RuleRegistry | None = None,
        config: LintConfig | None = None,
    ) -> None:
        """Initialize the linting engine.

        Args:
            registry: Rule registry (creates default if not provided)
            config: Linting configuration (uses default if not provided)
        """
        self.registry = registry or RuleRegistry()
        self.config = config or LintConfig()

        # Initialize tree-sitter parser
        self.parser = Parser(Language(tsmatlab.language()))

        # Load built-in rules
        self._load_builtin_rules()

        # Apply configuration to rules
        self._apply_config()

    def _load_builtin_rules(self) -> None:
        """Load built-in rules from the rules directory."""
        # Get the rules directory
        rules_dir = Path(__file__).parent.parent / "rules"
        if rules_dir.exists():
            self.registry.load_rules_from_directory(rules_dir)
            logger.debug(f"Loaded {len(self.registry.rules)} rules from {rules_dir}")
        else:
            logger.warning(f"Rules directory not found: {rules_dir}")

    def _apply_config(self) -> None:
        """Apply configuration to enable/disable rules."""
        for rule_id in self.registry.rules:
            if self.config.is_rule_enabled(rule_id):
                self.registry.enable_rule(rule_id)
            else:
                self.registry.disable_rule(rule_id)

    def lint_file(self, filepath: Path) -> list[Violation]:
        """Lint a single MATLAB file.

        Args:
            filepath: Path to the MATLAB file

        Returns:
            List of violations found
        """
        violations: list[Violation] = []

        # Check if file should be excluded
        if self.config.is_path_excluded(filepath):
            logger.debug(f"Skipping excluded file: {filepath}")
            return violations

        # Read the file
        try:
            source_bytes = filepath.read_bytes()
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return violations

        # Parse the file
        tree = self.parser.parse(source_bytes)
        root_node = tree.root_node

        # Check against all enabled rules
        enabled_rules = self.registry.get_enabled_rules()
        logger.debug(f"Checking {filepath} against {len(enabled_rules)} rules")

        for rule in enabled_rules:
            try:
                rule_violations = self._check_rule(rule, root_node, source_bytes, filepath)
                violations.extend(rule_violations)
            except Exception as e:
                logger.error(f"Error checking rule {rule.id} on {filepath}: {e}")

        return violations

    def _check_rule(
        self,
        rule: object,
        node: object,
        source_bytes: bytes,
        filepath: Path,
    ) -> list[Violation]:
        """Check a single rule against a file.

        Args:
            rule: Rule to check
            node: Root tree-sitter node
            source_bytes: Source code as bytes
            filepath: Path to the file being checked

        Returns:
            List of violations found
        """
        from maxx.lint.rule import Rule

        # Type assertion for mypy
        assert isinstance(rule, Rule)

        violations: list[Violation] = []

        # Get matches from the rule's query
        matches = rule.check_node(node, source_bytes)  # type: ignore[arg-type]

        for match in matches:
            # Get the first captured node for location info
            first_node = next(iter(match.values()))

            # Extract node text
            node_text = source_bytes[first_node.start_byte : first_node.end_byte].decode(
                "utf-8", errors="replace"
            )

            # Format message with captured variables
            message_vars = {
                "name": node_text,
                "line": first_node.start_point[0] + 1,
                "column": first_node.start_point[1],
            }
            # Add all captured nodes as variables
            for capture_name, capture_node in match.items():
                capture_text = source_bytes[capture_node.start_byte : capture_node.end_byte].decode(
                    "utf-8", errors="replace"
                )
                message_vars[capture_name] = capture_text

            try:
                message = rule.format_message(**message_vars)
            except KeyError as e:
                # Fallback if template variables don't match
                message = f"{rule.description}: {node_text}"
                logger.warning(f"Message template error in {rule.id}: {e}")

            violation = Violation(
                rule=rule,
                filepath=filepath,
                line=first_node.start_point[0] + 1,
                column=first_node.start_point[1],
                message=message,
                node_text=node_text,
            )
            violations.append(violation)

        return violations

    def lint_paths(
        self,
        paths: list[Path],
        recursive: bool = True,
    ) -> list[Violation]:
        """Lint multiple paths using PathsCollection.

        Args:
            paths: List of paths to lint (files or directories)
            recursive: Whether to recursively search directories

        Returns:
            List of all violations found
        """
        violations: list[Violation] = []

        # Collect all MATLAB files
        matlab_files: list[Path] = []

        for path in paths:
            if path.is_file():
                if path.suffix == ".m":
                    matlab_files.append(path)
            elif path.is_dir():
                # Use PathsCollection to find all MATLAB files
                try:
                    collection = PathsCollection([path], recursive=recursive)
                    # Get all file paths from the collection
                    for filepath in collection._objects.keys():
                        if filepath.suffix == ".m" and filepath.exists():
                            matlab_files.append(filepath)
                except Exception as e:
                    logger.error(f"Failed to collect files from {path}: {e}")

        logger.info(f"Linting {len(matlab_files)} MATLAB files")

        # Lint each file
        for filepath in matlab_files:
            file_violations = self.lint_file(filepath)
            violations.extend(file_violations)

        return violations

    def print_violations(
        self,
        violations: list[Violation],
        verbose: bool = False,
    ) -> None:
        """Print violations in a human-readable format.

        Args:
            violations: List of violations to print
            verbose: Whether to include additional details
        """
        if not violations:
            logger.info("No violations found!")
            return

        # Group violations by file
        by_file: dict[Path, list[Violation]] = {}
        for violation in violations:
            if violation.filepath not in by_file:
                by_file[violation.filepath] = []
            by_file[violation.filepath].append(violation)

        # Print violations grouped by file
        for filepath in sorted(by_file.keys()):
            file_violations = by_file[filepath]
            print(f"\n{filepath}")
            for violation in sorted(file_violations, key=lambda v: (v.line, v.column)):
                print(f"  {violation}")
                if verbose and violation.node_text:
                    print(f"    → {violation.node_text}")

        # Print summary
        total = len(violations)
        files = len(by_file)
        print(f"\nFound {total} violation(s) in {files} file(s)")
