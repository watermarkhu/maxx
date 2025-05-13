"""This module defines enumerations used by Malt."""

from __future__ import annotations

from enum import Enum
from typing import Literal


class Kind(str, Enum):
    """
    An enumeration representing different kinds of MATLAB code elements.
    This enumeration is a subclass of the Griffe `Kind` enumeration, and extends it with additional values.
    """

    FOLDER: Literal["folder"] = "folder"
    """folders"""
    NAMESPACE: Literal["namespace"] = "namespace"
    """namespaces"""
    CLASS: Literal["class"] = "class"
    """Classes."""
    FUNCTION: Literal["function"] = "function"
    """Functions and methods."""
    SCRIPT: Literal["script"] = "script"
    """Scripts."""
    PROPERTY: Literal["property"] = "property"
    """Class properties."""
    ALIAS: Literal["alias"] = "alias"
    """Aliases (imported objects)."""
    BUILTIN: Literal["builtin"] = "builtin"
    """Built-in objects."""


class ArgumentKind(str, Enum):
    """
    An enumeration representing different kinds of function arguments.

    Attributes:
        positional (str): Positional-only argument.
        optional (str): Optional argument.
        keyword_only (str): Keyword-only argument.
        varargin (str): Varargin argument.
    """

    positional_only: Literal["positional-only"] = "positional-only"
    optional: Literal["optional"] = "optional"
    keyword_only: Literal["keyword-only"] = "keyword-only"
    varargin: Literal["varargin"] = "varargin"


class AccessKind(str, Enum):
    """
    An enumeration representing different access levels for MATLAB code elements.

    Attributes:
        public (str): Represents public access level.
        protected (str): Represents protected access level.
        private (str): Represents private access level.
        immutable (str): Represents immutable access level.
    """

    public: Literal["public"] = "public"
    protected: Literal["protected"] = "protected"
    private: Literal["private"] = "private"
    immutable: Literal["immutable"] = "immutable"
