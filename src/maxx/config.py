"""Configuration classes for the maxx parser."""

from __future__ import annotations

import attrs

__all__ = ["ParserConfig"]


@attrs.frozen
class ParserConfig:
    """Configuration for the MATLAB file parser.

    This class controls various parsing behaviors, such as the placement
    of docstrings relative to definitions.

    Attributes:
        docstring_before_properties: If True, docstrings for properties must
            come BEFORE the property definition. If False (default), docstrings
            come AFTER the property definition.
        docstring_before_arguments: If True, docstrings for function arguments must
            come BEFORE the argument definition. If False (default), docstrings
            come AFTER the argument definition.
        docstring_before_enumerations: If True, docstrings for enumerations must
            come BEFORE the enumeration definition. If False (default), docstrings
            come AFTER the enumeration definition.
    """

    docstring_before_properties: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )
    docstring_before_arguments: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )
    docstring_before_enumerations: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )
