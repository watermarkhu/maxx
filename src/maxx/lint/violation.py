"""Violation data model for linting results."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from maxx.lint.rule import Rule


class Violation(BaseModel):
    """Represents a single linting violation.

    Attributes:
        rule: The rule that was violated
        filepath: Path to the file containing the violation
        line: Line number where the violation occurred
        column: Column number where the violation occurred (0-indexed)
        message: Human-readable violation message
        node_text: The text of the violating node (optional)
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    rule: Rule
    filepath: Path
    line: int = Field(ge=1, description="Line number (1-indexed)")
    column: int = Field(ge=0, description="Column number (0-indexed)")
    message: str = Field(min_length=1, description="Violation message")
    node_text: str | None = Field(default=None, description="The violating node text")

    def __str__(self) -> str:
        """Format violation for display."""
        location = f"{self.filepath}:{self.line}:{self.column + 1}"
        severity = self.rule.severity.upper()
        return f"{location}: {severity}[{self.rule.id}] {self.message}"

    def to_dict(self) -> dict[str, str | int]:
        """Convert violation to dictionary format."""
        return {
            "rule_id": self.rule.id,
            "rule_name": self.rule.name,
            "severity": self.rule.severity,
            "filepath": str(self.filepath),
            "line": self.line,
            "column": self.column + 1,  # Display as 1-indexed
            "message": self.message,
            "node_text": self.node_text or "",
        }
