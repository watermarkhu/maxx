"""This module defines exceptions used by Malt."""

from __future__ import annotations


class MaltError(Exception):
    """The base exception for all Malt errors."""


class CyclicAliasError(MaltError):
    """Exception raised when a cycle is detected in aliases."""

    def __init__(self, chain: list[str]) -> None:
        """Initialize the exception.

        Parameters:
            chain: The cyclic chain of items (such as target path).
        """
        self.chain: list[str] = chain
        """The chain of aliases that created the cycle."""

        super().__init__("Cyclic aliases detected:\n  " + "\n  ".join(self.chain))


class FilePathError(MaltError):
    """Exception raised when trying to access the filepath of an object."""


class NameResolutionError(MaltError):
    """Exception for names that cannot be resolved in a object scope."""
