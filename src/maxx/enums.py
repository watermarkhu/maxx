"""This module defines enumerations used by Malt."""

from __future__ import annotations

from enum import Enum


class Kind(str, Enum):
    """
    An enumeration representing different kinds of MATLAB code elements.
    This enumeration is a subclass of the Griffe `Kind` enumeration, and extends it with additional values.
    """

    FOLDER = "folder"
    """folders"""
    NAMESPACE = "namespace"
    """namespaces"""
    CLASS = "class"
    """Classes."""
    ENUMERATION = "class"
    """Class enumeration"""
    FUNCTION = "function"
    """Functions and methods."""
    SCRIPT = "script"
    """Scripts."""
    PROPERTY = "property"
    """Class properties."""
    ALIAS = "alias"
    """Aliases (imported objects)."""
    BUILTIN = "builtin"
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

    positional_only = "positional-only"
    optional = "optional"
    keyword_only = "keyword-only"
    varargin = "varargin"


class AccessKind(str, Enum):
    """
    An enumeration representing different access levels for MATLAB code elements.

    Attributes:
        public (str): Represents public access level.
        protected (str): Represents protected access level.
        private (str): Represents private access level.
        immutable (str): Represents immutable access level.
    """

    public = "public"
    protected = "protected"
    private = "private"
    immutable = "immutable"
