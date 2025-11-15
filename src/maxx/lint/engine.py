"""Core linting engine for MATLAB code analysis."""

from __future__ import annotations

import json
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

            # Apply custom validation logic for specific rules
            should_report = self._apply_custom_validation(
                rule, match, source_bytes, filepath, message_vars
            )

            if not should_report:
                continue

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

            # Log the violation with loguru
            log_msg = f"{filepath}:{violation.line}:{violation.column + 1} - {rule.severity.upper()}[{rule.id}] {message}"
            if rule.severity == "error":
                logger.error(log_msg)
            elif rule.severity == "warning":
                logger.warning(log_msg)
            else:  # info
                logger.info(log_msg)

        return violations

    def _apply_custom_validation(
        self,
        rule: object,
        match: object,
        source_bytes: bytes,
        filepath: Path,
        message_vars: dict[str, object],
    ) -> bool:
        """Apply custom validation logic for specific rules.

        Args:
            rule: Rule being checked
            match: Matched nodes from query
            source_bytes: Source code as bytes
            filepath: Path to the file being checked
            message_vars: Variables for message formatting (will be updated)

        Returns:
            True if violation should be reported, False otherwise
        """
        from maxx.lint.rule import Rule

        assert isinstance(rule, Rule)

        # Name length validation rules (MW-N001, MW-N003 - MW-N006)
        if rule.id in ("MW-N001", "MW-N003", "MW-N004", "MW-N005", "MW-N006"):
            # Get the name from the appropriate capture
            name_key = {
                "MW-N001": "var_name",
                "MW-N003": "function_name",
                "MW-N004": "class_name",
                "MW-N005": "method_name",
                "MW-N006": "property_name",
            }.get(rule.id)

            if name_key and name_key in message_vars:
                name = str(message_vars[name_key])
                if len(name) <= 32:
                    return False  # Name is within limit, don't report
                message_vars["length"] = len(name)

        # File name matching validation (MW-N002, MW-C001)
        elif rule.id in ("MW-N002", "MW-C001"):
            name_key = "function_name" if rule.id == "MW-N002" else "class_name"
            if name_key in message_vars:
                name = str(message_vars[name_key])
                filename = filepath.stem
                if name.lower() == filename.lower():
                    return False  # Names match, don't report

        # Function input/output count validation (MW-F002, MW-F003)
        elif rule.id in ("MW-F002", "MW-F003"):
            # For now, report all functions for manual review
            # Full implementation would require counting parameters in the AST
            pass

        # Line length validation (MW-L001)
        elif rule.id == "MW-L001":
            # Check line length from source
            import re

            source_lines = source_bytes.decode("utf-8", errors="replace").split("\n")
            for line_num, line in enumerate(source_lines, 1):
                if len(line) > 120:
                    message_vars["line"] = line_num
                    message_vars["length"] = len(line)
                    # Return True to report this specific line
                    # Note: This will only report the first long line
                    return True
            return False  # No long lines found

        # Naming casing validation (MW-N007 - MW-N010)
        elif rule.id in ("MW-N007", "MW-N008", "MW-N009", "MW-N010"):
            import re

            name_key = {
                "MW-N007": "var_name",
                "MW-N008": "function_name",
                "MW-N009": "property_name",
                "MW-N010": "method_name",
            }.get(rule.id)

            if name_key and name_key in message_vars:
                name = str(message_vars[name_key])

                # Check casing based on rule
                if rule.id in ("MW-N007", "MW-N008", "MW-N010"):
                    # lowerCamelCase or lowercase
                    # Valid: lowercase, lowerCamelCase
                    # Invalid: UpperCamelCase, snake_case, UPPERCASE
                    if re.match(r"^[a-z][a-zA-Z0-9]*$", name):
                        return False  # Valid casing
                elif rule.id == "MW-N009":
                    # UpperCamelCase for properties
                    # Valid: UpperCamelCase
                    # Invalid: lowerCamelCase, snake_case
                    if re.match(r"^[A-Z][a-zA-Z0-9]*$", name):
                        return False  # Valid casing

        # Special rules that need custom handling
        elif rule.id == "MW-S001":
            # Loop iterator modification - requires manual review
            # Keep this as an informational warning
            pass

        return True  # Report the violation

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

    def export_violations_to_json(
        self,
        violations: list[Violation],
        output_path: Path,
    ) -> None:
        """Export violations to a JSON file.

        Args:
            violations: List of violations to export
            output_path: Path to the output JSON file
        """
        # Convert violations to dictionaries
        violations_data = [v.to_dict() for v in violations]

        # Create summary data
        summary = {
            "total_violations": len(violations),
            "total_files": len(set(v.filepath for v in violations)),
            "by_severity": {},
            "by_rule": {},
        }

        # Count violations by severity and rule
        for violation in violations:
            severity = violation.rule.severity
            rule_id = violation.rule.id

            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            summary["by_rule"][rule_id] = summary["by_rule"].get(rule_id, 0) + 1

        # Create output structure
        output = {
            "summary": summary,
            "violations": violations_data,
        }

        # Write to file
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        logger.info(f"Exported {len(violations)} violations to {output_path}")
