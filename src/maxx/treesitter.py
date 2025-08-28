"""Tree-sitter queries to extract information from MATLAB files."""

from __future__ import annotations

import textwrap
import warnings
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import charset_normalizer
import tree_sitter_matlab as tsmatlab
from tree_sitter import Language, Node, Parser, Query, QueryCursor, Tree, TreeCursor

from maxx.enums import AccessKind, ArgumentKind
from maxx.expressions import Expr
from maxx.objects import (
    Argument,
    Arguments,
    Class,
    Docstring,
    Enumeration,
    Function,
    Property,
    Script,
)

if TYPE_CHECKING:
    from maxx.collection import PathsCollection


__all__ = ["FileParser"]


with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    LANGUAGE = Language(tsmatlab.language())
PARSER = Parser(LANGUAGE)

FILE_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """(source_file .
    (comment)* @header .
    [
        (function_definition) @function
        (class_definition) @type
    ]?
)
""",
    )
)


FUNCTION_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """(function_definition .
    ("function")
    (function_output .
        [
            (identifier) @output
            (multioutput_variable .
                [
                    (identifier) @output
                    _
                ]*
            )
        ]
    )?
    [
        ("set.") @setter
        ("get.") @getter
    ]?
    (identifier) @name
    (function_arguments .
        [
            (identifier) @input
            _
        ]*
    )?
    (comment)* @docstring
    (arguments_statement)* @arguments
)""",
    )
)


ARGUMENTS_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """(arguments_statement .
    ("arguments")
    (attributes
        (identifier) @attributes
    )?
    (comment)?
    ("\\n")?
    (property)+ @arguments
)""",
    )
)


PROPERTY_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """(property .
    [
        (identifier) @name
        (property_name
            (identifier) @options .
            (".") .
            (identifier) @name
        )
    ]
    (dimensions
        [
            (number) @dimensions
            (spread_operator) @dimensions
            _
        ]*
    )?
    [
        (identifier)
        (property_name)
    ]? @type
    (validation_functions)? @validators
    (default_value
        ("=")
        _+ @default
    )?
    (comment)* @comment
)""",
    )
)


ATTRIBUTE_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """(attribute
    (identifier) @name
    (
        ("=")
        _+ @value
    )?
)""",
    )
)


CLASS_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """("classdef" .
    (attributes
        (attribute) @attributes
    )?
    (identifier) @name
    (superclasses
        (property_name) @bases
    )? .
    (comment)* @docstring
    ("\\n")?
    [
        (comment)
        (methods) @methods
        (properties) @properties
        (enumeration) @enumeration
    ]*
)""",
    )
)


METHODS_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """("methods" .
    (attributes
        (attribute) @attributes
    )? .
    (
        ("\\n")* .
        (function_definition)* @methods
    )*
)""",
    )
)

PROPERTIES_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """("properties" .
    (attributes
        (attribute) @attributes
    )? .
    (
        ("\\n")* .
        (property)* @properties
    )*
)""",
    )
)

ENUMERATIONS_QUERY = QueryCursor(
    Query(
        LANGUAGE,
        """("enumeration" .
    (
        ("\\n")* .
        (enum
            (identifier) @content
            (
                ("(")
                (_)+ @content
                (")")
            )?
        ) .
        ("\\n")* .
        (comment)* @content
    )*
)""",
    )
)


def _strtobool(value: str) -> bool:
    """
    Convert a string representation of truth to boolean.

    Args:
        value: The string to convert. Expected values are "true", "1" for True, and any other value for False.

    Returns:
        True if the input string is "true" or "1" (case insensitive), otherwise False.
    """
    if value.lower() in ["true", "1"]:
        return True
    else:
        return False


def _dedent(lines: list[str]) -> list[str]:
    """
    Remove the common leading whitespace from each line in the given list of lines.

    Args:
        lines: A list of strings where each string represents a line of text.

    Returns:
        A list of strings with the common leading whitespace removed from each line.
    """
    text = "\n".join(lines)
    dedented_text = textwrap.dedent(text)
    return dedented_text.split("\n")


def _sort_nodes(nodes: list[Node]) -> list[Node]:
    """
    Sort a list of nodes based on their start point.

    Args:
        nodes: A list of Node objects to be sorted.

    Returns:
        A new list of Node objects sorted by their start point.
    """
    return sorted(nodes, key=lambda node: node.start_point)


class FileParser(object):
    """
    A class to parse MATLAB files using Tree-sitter.

    Attributes:
        filepath (Path): The path to the MATLAB file.
        encoding (str): The encoding of the file content.
        content: Returns the decoded content of the file.

    Methods:
        parse(**kwargs) -> Object: Parses the MATLAB file and returns a Object.
    """

    def __init__(self, filepath: Path, paths_collection: "PathsCollection | None" = None) -> None:
        """
        Initialize the object with the given file path.

        Args:
            filepath (Path): The path to the file to be processed.
        """
        self.filepath: Path = filepath
        self.paths_collection: PathsCollection | None = paths_collection
        result = charset_normalizer.from_path(filepath).best()
        self.encoding: str = result.encoding if result else "utf-8"
        with open(filepath, "rb") as f:
            self._content: bytes = f.read()
        self._node: Node | None = None

    @property
    def content(self):
        """
        Property that decodes and returns the content using the specified encoding.

        Returns:
            str: The decoded content.
        """
        return self._content.decode(self.encoding)

    def parse(self, **kwargs: Any) -> Function | Class | Script:
        """
        Parse the content of the file and return a Object.

        This method uses a tree-sitter parser to parse the content of the file
        and extract relevant information to create a Object. It handles
        different types of Matlab constructs such as functions and classes.

        Args:
            **kwargs: Additional keyword arguments to pass to the parsing methods.

        Returns:
            Object: An instance of Object representing the parsed content.

        Raises:
            ValueError: If the file could not be parsed.
        """
        try:
            tree: Tree = PARSER.parse(self._content)
            cursor: TreeCursor = tree.walk()
            node: Node | None = cursor.node

            if node is None:
                raise ValueError(f"The file {self.filepath} could not be parsed.")
            captures = FILE_QUERY.captures(node)

            if TYPE_CHECKING:
                object: Function | Class | Script | None = None
            if "function" in captures:
                object = self._parse_function(captures["function"][0], **kwargs)
            elif "type" in captures:
                object = self._parse_class(captures["type"][0], **kwargs)
            else:
                object = Script(self.filepath.stem, filepath=self.filepath, node=node, **kwargs)

            if not object.docstring:
                object.docstring = self._comment_docstring(
                    captures.get("header", None), parent=object
                )

            return object

        except Exception as ex:
            syntax_error = SyntaxError("Error parsing Matlab file")
            syntax_error.filename = str(self.filepath)
            if self._node is not None:
                if self._node.text is not None:
                    indentation: str = " " * self._node.start_point.column
                    syntax_error.text = indentation + self._node.text.decode(self.encoding)
                syntax_error.lineno = self._node.start_point.row + 1
                syntax_error.offset = self._node.start_point.column + 1
                syntax_error.end_lineno = self._node.end_point.row + 1
                syntax_error.end_offset = self._node.end_point.column + 1
            raise syntax_error from ex

    def _parse_class(self, node: Node, **kwargs: Any) -> Class:
        """
        Parse a class node and return a Class or Class object.

        This method processes a class node captured by the CLASS_QUERY and extracts
        its bases, docstring, attributes, properties, and methods. It constructs
        and returns a Class or Class object based on the parsed information.

        Args:
            node (Node): The class node to parse.
            **kwargs: Additional keyword arguments to pass to the Class or Class object.

        Returns:
            Class: The parsed Class or Class object.
        """
        self._node = node
        saved_kwargs = {key: value for key, value in kwargs.items()}
        captures = CLASS_QUERY.captures(node)

        bases = self._decode_from_capture(captures, "bases")
        docstring = self._comment_docstring(captures.get("docstring", None))

        attribute_pairs = [self._parse_attribute(node) for node in captures.get("attributes", [])]
        for key, value in attribute_pairs:
            if key in ["Sealed", "Abstract", "Hidden"]:
                kwargs[key] = value

        object = Class(
            self.filepath.stem,
            lineno=node.range.start_point.row + 1,
            endlineno=node.range.end_point.row + 1,
            node=node,
            bases=bases,
            docstring=docstring,
            filepath=self.filepath,
            **kwargs,
        )

        def add_enum(identifier, comment_nodes, value_nodes):
            docstring = (
                self._comment_docstring(comment_nodes, parent=object) if comment_nodes else None
            )
            value = Expr(value_nodes, self.encoding) if value_nodes else None
            enumeration = Enumeration(identifier, docstring=docstring, parent=object, value=value)
            object.members[enumeration.name] = enumeration

        for enumeration_captures in [
            ENUMERATIONS_QUERY.captures(n) for n in _sort_nodes(captures.get("enumeration", []))
        ]:
            identifier: str = ""
            comment_nodes: list[Node] = []
            value_nodes: list[Node] = []

            for n in _sort_nodes(enumeration_captures["content"]):
                match n.type:
                    case "identifier":
                        if identifier:
                            add_enum(identifier, comment_nodes, value_nodes)
                        identifier: str = self._decode(n)
                        comment_nodes = []
                        value_nodes = []
                    case "comment":
                        comment_nodes.append(n)
                    case _:
                        value_nodes.append(n)
            else:
                if identifier:
                    add_enum(identifier, comment_nodes, value_nodes)

        for property_captures in [
            PROPERTIES_QUERY.captures(n) for n in _sort_nodes(captures.get("properties", []))
        ]:
            property_kwargs = {key: value for key, value in saved_kwargs.items()}
            attribute_pairs = [
                self._parse_attribute(n) for n in property_captures.get("attributes", [])
            ]
            for key, value in attribute_pairs:
                if key in [
                    "AbortSet",
                    "Abstract",
                    "Constant",
                    "Dependant",
                    "GetObservable",
                    "Hidden",
                    "NonCopyable",
                    "SetObservable",
                    "Transient",
                    "WeakHandle",
                ]:
                    property_kwargs[key] = value
                elif key in ["Access", "GetAccess", "SetAccess"]:
                    if value in ["public", "protected", "private", "immutable"]:
                        property_kwargs[key] = AccessKind(value)
                    else:
                        property_kwargs[key] = AccessKind.private
            for property_node in property_captures.get("properties", []):
                property_captures = PROPERTY_QUERY.captures(property_node)

                prop = Property(
                    self._first_from_capture(property_captures, "name"),
                    dimensions=self._decode_from_capture(property_captures, "dimensions")
                    if "dimensions" in property_captures
                    else None,
                    type=Expr(property_captures["type"], self.encoding)
                    if "type" in property_captures
                    else None,
                    validators=Expr(property_captures["validators"], self.encoding)
                    if "validators" in property_captures
                    else None,
                    default=Expr(property_captures["default"], self.encoding)
                    if "default" in property_captures
                    else None,
                    docstring=self._comment_docstring(
                        property_captures.get("comment", None), parent=object
                    ),
                    parent=object,
                    node=property_node,
                    **property_kwargs,
                )
                object.members[prop.name] = prop

        for method_captures in [
            METHODS_QUERY.captures(n) for n in _sort_nodes(captures.get("methods", []))
        ]:
            method_kwargs = {key: value for key, value in saved_kwargs.items()}
            attribute_pairs = [
                self._parse_attribute(n) for n in method_captures.get("attributes", [])
            ]
            for key, value in attribute_pairs:
                if key in [
                    "Abstract",
                    "Hidden",
                    "Sealed",
                    "Static",
                ]:
                    method_kwargs[key] = value
                elif key == "Access":
                    if value in ["public", "protected", "private", "immutable"]:
                        method_kwargs[key] = AccessKind(value)
                    else:
                        method_kwargs[key] = AccessKind.private
            for method_node in method_captures.get("methods", []):
                method = self._parse_function(
                    method_node, method=True, parent=object, **method_kwargs
                )
                if method.name != self.filepath.stem and not method.Static and method.arguments:
                    # Remove self from first method capture_argument
                    method.arguments._args = method.arguments._args[1:]
                if method.is_getter and method.name in object.members:
                    prop = object.members[method.name]
                    if isinstance(prop, Property):
                        prop.getter = method
                    else:
                        # This can be either an error or that it is a getter in an inherited class
                        pass
                elif method.is_setter and method.name in object.members:
                    prop = object.members[method.name]
                    if isinstance(prop, Property):
                        prop.setter = method
                    else:
                        # This can be either an error or that it is a setter in an inherited class
                        pass
                else:
                    object.members[method.name] = method

        return object

    def _parse_attribute(self, node: Node) -> tuple[str, Any]:
        """
        Parse an attribute from a given node.

        Args:
            node (Node): The node to parse the attribute from.

        Returns:
            tuple[str, Any]: A tuple containing the attribute key and its value.
                             The value is `True` if no value is specified,
                             otherwise it is the parsed value which can be a boolean or a string.
        """
        self._node = node
        captures = ATTRIBUTE_QUERY.captures(node)

        key = self._first_from_capture(captures, "name")
        if TYPE_CHECKING:
            value: bool | str = ""
        if "value" not in captures:
            value = True
        elif captures["value"][0].type == "boolean":
            value = _strtobool(self._first_from_capture(captures, "value"))
        else:
            value = self._first_from_capture(captures, "value")

        return (key, value)

    def _parse_function(self, node: Node, method: bool = False, **kwargs: Any) -> Function:
        """
        Parse a function node and return a Function object.

        Args:
            node (Node): The node representing the function in the syntax tree.
            method (bool, optional): Whether the function is a method. Defaults to False.
            **kwargs: Additional keyword arguments to pass to the Function object.

        Returns:
            Function: The parsed function object.

        Raises:
            KeyError: If required captures are missing from the node.

        """
        self._node = node
        captures: dict = FUNCTION_QUERY.matches(node)[0][1]

        input_names = self._decode_from_capture(captures, "input")
        arguments: dict = (
            OrderedDict(
                (name, Argument(name, kind=ArgumentKind.positional_only)) for name in input_names
            )
            if input_names
            else {}
        )
        output_names = self._decode_from_capture(captures, "output")
        returns: dict = (
            OrderedDict(
                (name, Argument(name, kind=ArgumentKind.positional_only)) for name in output_names
            )
            if output_names
            else {}
        )
        if method:
            function_name = self._first_from_capture(captures, "name")
        else:
            function_name = self.filepath.stem

        object: Function = Function(
            function_name,
            lineno=node.range.start_point.row + 1,
            endlineno=node.range.end_point.row + 1,
            filepath=self.filepath,
            docstring=self._comment_docstring(captures.get("docstring", None)),
            getter="getter" in captures,
            setter="setter" in captures,
            node=node,
            **kwargs,
        )

        captures_arguments = [
            ARGUMENTS_QUERY.captures(node) for node in captures.get("arguments", [])
        ]
        for capture_arguments in captures_arguments:
            attributes = self._decode_from_capture(capture_arguments, "attributes")
            is_input = attributes is None or "Input" in attributes or "Output" not in attributes
            # is_repeating = "Repeating" in attributes

            for argument_node in _sort_nodes(capture_arguments["arguments"]):
                capture_argument = PROPERTY_QUERY.captures(argument_node)
                arg_name = self._first_from_capture(capture_argument, "name")

                if "options" in capture_argument:
                    options_name = self._first_from_capture(capture_argument, "options")
                    arguments.pop(options_name, None)
                    argument = arguments[arg_name] = Argument(
                        arg_name, kind=ArgumentKind.keyword_only, node=argument_node
                    )
                else:
                    if is_input:
                        argument = arguments.get(arg_name, Argument(arg_name))
                    else:
                        argument = returns.get(arg_name, Argument(arg_name))

                    if "default" in capture_argument:
                        argument.kind = ArgumentKind.optional
                    else:
                        argument.kind = ArgumentKind.positional_only

                if "dimensions" in capture_argument:
                    argument.dimensions = self._decode_from_capture(capture_argument, "dimensions")

                if "type" in capture_argument:
                    argument.type = Expr(capture_argument["type"], self.encoding)

                if "validators" in capture_argument:
                    argument.validators = Expr(capture_argument["validators"], self.encoding)

                if "default" in capture_argument:
                    argument.default = Expr(capture_argument["default"], self.encoding)

                docstring = self._comment_docstring(
                    capture_argument.get("comment", None), parent=object
                )
                if docstring:
                    argument.docstring = docstring

        object.arguments = Arguments(*list(arguments.values()))
        if returns:
            object.returns = Arguments(*list(returns.values()))
        return object

    def _decode(self, node: Node) -> str:
        """
        Decode the text of a given node using the specified encoding.

        Args:
            node: The node whose text needs to be decoded.

        Returns:
            The decoded text of the node. If the node or its text is None, returns an empty string.
        """
        self._node = node
        return node.text.decode(self.encoding) if node is not None and node.text is not None else ""

    def _decode_from_capture(self, capture: dict[str, list[Node]], key: str) -> list[str]:
        """
        Decode elements from a capture dictionary based on a specified key.

        Args:
            capture: A dictionary where the keys are strings and the values are lists of Node objects.
            key: The key to look for in the capture dictionary.

        Returns:
            A list of decoded strings corresponding to the elements associated with the specified key in the capture dictionary.
        """
        if key not in capture:
            return []
        else:
            return [self._decode(element) for element in capture[key]]

    def _first_from_capture(self, capture: dict[str, list[Node]], key: str) -> str:
        """
        Retrieve the first decoded string from a capture dictionary for a given key.

        Args:
            capture: A dictionary where the key is a string and the value is a list of Node objects.
            key: The key to look up in the capture dictionary.

        Returns:
            The first decoded string if available, otherwise an empty string.
        """
        decoded = self._decode_from_capture(capture, key)
        if decoded:
            return decoded[0]
        else:
            return ""

    def _comment_docstring(
        self, nodes: list[Node] | Node | None, parent: Any = None
    ) -> Docstring | None:
        """
        Extract and process a docstring from given nodes.

        This method processes nodes to extract a docstring, handling different
        comment styles and blocks. It supports both single-line and multi-line
        comments, as well as special comment blocks delimited by `%{` and `%}`.

        Args:
            nodes (list[Node] | Node | None): The nodes from which to extract the docstring.

        Returns:
            Docstring | None: The extracted and processed docstring, or None if no docstring is found.

        Raises:
            LookupError: If a line does not start with a comment character.
        """
        if nodes is None:
            return None
        elif isinstance(nodes, list):
            # Ensure that if there is a gap between subsequent comment nodes, only the first block is considered
            if gaps := (
                end.start_point.row - start.end_point.row
                for (start, end) in zip(nodes[:-1], nodes[1:])
            ):
                first_gap_index = next((i for i, gap in enumerate(gaps) if gap > 1), None)
                nodes = nodes[: first_gap_index + 1] if first_gap_index is not None else nodes

            lineno = nodes[0].range.start_point.row + 1
            endlineno = nodes[-1].range.end_point.row + 1
            lines = iter(
                [
                    line
                    for lines in [self._decode(node).splitlines() for node in nodes]
                    for line in lines
                ]
            )
        elif isinstance(nodes, Node):
            lineno = nodes.range.start_point.row + 1
            endlineno = nodes.range.end_point.row + 1
            lines = iter(self._decode(nodes).splitlines())

        docstring: list[str] = []
        uncommented: list[str] = []

        while True:
            try:
                line = next(lines).lstrip()
            except StopIteration:
                break

            # Exclude all pragma's
            if line in [
                "%#codegen",
                "%#eml",
                "%#external",
                "%#exclude",
                "%#function",
                "%#ok",
                "%#mex",
            ]:
                continue

            if "--8<--" in line:
                continue

            if line[:2] == "%{" or line[:2] == "%%":
                if uncommented:
                    docstring += _dedent(uncommented)
                    uncommented = []
                if line[:2] == "%%":
                    docstring.append(line[2:].lstrip())
                    continue

                comment_block = []
                line = line[2:]
                while "%}" not in line:
                    comment_block.append(line)
                    try:
                        line = next(lines)
                    except StopIteration:
                        break
                else:
                    last_line = line[: line.index("%}")]
                    if last_line:
                        comment_block.append(last_line)
                docstring.append(comment_block[0])
                docstring += _dedent(comment_block[1:])

            elif line[0] == "%":
                uncommented.append(line[1:])
            else:
                raise LookupError

        if uncommented:
            docstring += _dedent(uncommented)

        return Docstring(
            "\n".join(docstring),
            lineno=lineno,
            endlineno=endlineno,
            parent=parent,
        )
