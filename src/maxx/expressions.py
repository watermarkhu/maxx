from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from tree_sitter import Node

__all__ = ["Expr", "MATLAB_BUILTINS"]


def _load_matlab_builtins() -> dict:
    """
    Load the MATLAB builtin functions from a JSON file.

    Returns:
        dict: A dictionary containing MATLAB builtin functions and their documentation URLs.
    """
    json_path: Path = Path(__file__).parent / "matlab_builtins.json"
    with open(json_path, "r") as file:
        return json.load(file)


MATLAB_BUILTINS: dict[str, str] = _load_matlab_builtins()
MATHWORKS_DOC_URL = "https://www.mathworks.com/help/matlab"


@dataclass
class Expr:
    nodes: list[Node]
    encoding: str

    def iterate(self) -> Iterator[str]:
        """Iterate over the values of the expression."""
        for node in self.nodes:
            if node.text:
                yield node.text.decode(self.encoding)

    def __str__(self) -> str:
        """Return the string representation of the builtin expression."""
        return "".join(elem for elem in self.iterate())

    def __iter__(self) -> Iterator[str]:
        """Iterate on the expression syntax and elements."""
        yield from self.iterate()

    @property
    def doc(self) -> str:
        for elem in self.iterate():
            if elem in MATLAB_BUILTINS:
                return f"{MATHWORKS_DOC_URL}/{MATLAB_BUILTINS[elem]}"
        return ""
