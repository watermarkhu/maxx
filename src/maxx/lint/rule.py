"""Rule definition and loading system for MATLAB linting."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from tree_sitter import Language, Node, Query, QueryCursor

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# Import tree-sitter-matlab language
import tree_sitter_matlab as tsmatlab


class Rule(BaseModel):
    """Represents a single linting rule.

    Attributes:
        id: Unique rule identifier (e.g., "W001")
        name: Rule name (e.g., "unused-variable")
        description: Human-readable description
        severity: Severity level ("error", "warning", "info")
        query: Tree-sitter query for pattern matching
        message_template: Template for violation messages
        enabled: Whether the rule is enabled by default
        filepath: Path to the TOML file defining this rule
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(min_length=1, description="Unique rule identifier")
    name: str = Field(min_length=1, description="Rule name")
    description: str = Field(min_length=1, description="Human-readable description")
    severity: Literal["error", "warning", "info"] = Field(
        default="warning", description="Severity level"
    )
    query: QueryCursor = Field(description="Tree-sitter query for pattern matching")
    message_template: str = Field(min_length=1, description="Template for violation messages")
    enabled: bool = Field(default=True, description="Whether the rule is enabled by default")
    filepath: Path | None = Field(default=None, description="Path to the TOML file")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        if v not in ("error", "warning", "info"):
            raise ValueError(f"Invalid severity: {v}. Must be 'error', 'warning', or 'info'")
        return v

    @classmethod
    def from_toml(cls, filepath: Path) -> Rule:
        """Load a rule from a TOML file.

        Args:
            filepath: Path to the TOML file

        Returns:
            Rule instance

        Raises:
            ValueError: If the TOML file is malformed or missing required fields
            ValidationError: If the rule data fails validation
        """
        with open(filepath, "rb") as f:
            data = tomllib.load(f)

        # Validate required sections
        if "rule" not in data:
            raise ValueError(f"Missing [rule] section in {filepath}")
        if "query" not in data:
            raise ValueError(f"Missing [query] section in {filepath}")
        if "message" not in data:
            raise ValueError(f"Missing [message] section in {filepath}")

        rule_data = data["rule"]
        query_data = data["query"]
        message_data = data["message"]

        # Validate required fields
        required_rule_fields = ["id", "name", "description"]
        for field in required_rule_fields:
            if field not in rule_data:
                raise ValueError(f"Missing required field [rule].{field} in {filepath}")

        if "pattern" not in query_data:
            raise ValueError(f"Missing required field [query].pattern in {filepath}")

        if "template" not in message_data:
            raise ValueError(f"Missing required field [message].template in {filepath}")

        # Get the MATLAB language
        language = Language(tsmatlab.language())

        # Create tree-sitter query
        try:
            query = QueryCursor(Query(language, query_data["pattern"]))
        except Exception as e:
            raise ValueError(f"Invalid tree-sitter query in {filepath}: {e}") from e

        # Use Pydantic's model_validate to create and validate the rule
        return cls.model_validate(
            {
                "id": rule_data["id"],
                "name": rule_data["name"],
                "description": rule_data["description"],
                "severity": rule_data.get("severity", "warning"),
                "query": query,
                "message_template": message_data["template"],
                "enabled": rule_data.get("enabled", True),
                "filepath": filepath,
            }
        )

    def check_node(self, node: Node, source_bytes: bytes) -> list[dict[str, Node]]:
        """Check a node against this rule's query.

        Args:
            node: Tree-sitter node to check
            source_bytes: Source code as bytes

        Returns:
            List of matches, where each match is a dict of capture names to a single node
        """
        # Use matches() method to get properly grouped captures
        # matches() returns list of (pattern_index, captures_dict) tuples
        query_matches = self.query.matches(node)  # type: ignore[attr-defined]
        if not query_matches:
            return []

        matches: list[dict[str, Node]] = []
        for _, captures_dict in query_matches:
            # captures_dict maps capture names to lists of nodes
            # We want a single dict mapping capture names to the first node
            match_dict: dict[str, Node] = {}
            for capture_name, node_list in captures_dict.items():
                if node_list:
                    match_dict[capture_name] = node_list[0]
            if match_dict:
                matches.append(match_dict)

        return matches

    def format_message(self, **kwargs: Any) -> str:
        """Format the violation message using the template.

        Args:
            **kwargs: Variables to substitute in the template

        Returns:
            Formatted message
        """
        return self.message_template.format(**kwargs)


class RuleRegistry:
    """Registry for managing linting rules."""

    def __init__(self) -> None:
        """Initialize the rule registry."""
        self.rules: dict[str, Rule] = {}

    def load_rule(self, filepath: Path) -> None:
        """Load a single rule from a TOML file.

        Args:
            filepath: Path to the rule TOML file
        """
        rule = Rule.from_toml(filepath)
        self.rules[rule.id] = rule

    def load_rules_from_directory(self, directory: Path) -> None:
        """Load all rules from a directory.

        Args:
            directory: Directory containing rule TOML files
        """
        if not directory.exists():
            return

        for filepath in sorted(directory.glob("*.toml")):
            try:
                self.load_rule(filepath)
            except Exception as e:
                # Log error but continue loading other rules
                from maxx.logger import logger

                logger.warning(f"Failed to load rule from {filepath}: {e}")

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            Rule instance or None if not found
        """
        return self.rules.get(rule_id)

    def get_enabled_rules(self) -> list[Rule]:
        """Get all enabled rules.

        Returns:
            List of enabled rules
        """
        return [rule for rule in self.rules.values() if rule.enabled]

    def get_all_rules(self) -> list[Rule]:
        """Get all rules.

        Returns:
            List of all rules
        """
        return list(self.rules.values())

    def enable_rule(self, rule_id: str) -> None:
        """Enable a rule by ID.

        Args:
            rule_id: Rule identifier
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True

    def disable_rule(self, rule_id: str) -> None:
        """Disable a rule by ID.

        Args:
            rule_id: Rule identifier
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
