from __future__ import annotations

import threading
from contextlib import suppress
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Callable, Sequence, cast

from griffe import Docstring
from griffe._internal.c3linear import c3linear_merge
from tree_sitter import Node

from maxx.enums import AccessKind, ArgumentKind, Kind
from maxx.exceptions import CyclicAliasError, FilePathError, NameResolutionError
from maxx.expressions import Expr
from maxx.logger import logger
from maxx.mixins import ObjectAliasMixin, PathMixin

if TYPE_CHECKING:
    from maxx.collection import LinesCollection, PathsCollection


class Validatable:
    """This class represent a Validable (argument / property)."""

    def __init__(
        self,
        name: str,
        *,
        type: Expr | str | None = None,
        dimensions: list[str] | None = None,
        default: Expr | str | None = None,
        docstring: Docstring | None = None,
        validators: Expr | str | None = None,
        parent: Object | None = None,
        node: Node | None = None,
        paths_collection: "PathsCollection | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the validatable.

        Parameters:
            name: The validatable name, without leading stars (`*` or `**`).
            type: The validatable type, if any.
            kind: The validatable kind.
            default: The validatable default, if any.
            docstring: The validatable docstring.
        """
        self.name: str = name
        """The validatable name."""
        self.type: Expr | str | None = type
        """The validatable type type."""
        self.dimensions: list[str] | None = dimensions
        """The validatable dimensions, if any."""
        self.validators: Expr | str | None = validators
        """The validatable validators, if any."""
        self.default: Expr | str | None = default
        """The validatable default value."""
        self.docstring: Docstring | None = docstring
        """The validatable docstring."""
        self.parent: Object | None = parent
        """The parent of the validatable (none if top module)."""
        self.node: Node | None = node
        """The tree-sitter node of the object."""
        self._paths_collection: "PathsCollection | None" = paths_collection

        # Attach the docstring to this object.
        if self.docstring is not None:
            self.docstring.parent = self

    @property
    def has_docstring(self) -> bool:
        """Whether this object has a docstring (empty or not)."""
        return bool(self.docstring)

    def __str__(self) -> str:
        arg = f"{self.name}: {self.type} = {self.default}"
        if hasattr(self, "kind") and self.kind is not None:
            return f"[{self.kind.value}] {arg}"
        return arg

    def __eq__(self, value: object, /) -> bool:
        """Arguments are equal if all their attributes except `docstring` and `function` are equal."""
        if not isinstance(value, Argument):
            return NotImplemented
        return (
            self.name == value.name
            and self.type == value.type
            and self.kind == value.kind
            and self.default == value.default
        )


class Argument(Validatable):
    """This class represent a function argument."""

    def __init__(self, *args, kind: ArgumentKind | None = None, **kwargs) -> None:
        """Initialize the argument."""
        super().__init__(*args, **kwargs)
        self.kind = kind
        """The argument kind."""

    def __repr__(self) -> str:
        return f"Argument(name={self.name!r}, type={self.type!r}, kind={self.kind!r}, default={self.default!r})"

    @property
    def required(self) -> bool:
        """Whether this argument is required."""
        return self.default is None


class Arguments:
    """This class is a container for arguments.

    It allows to get arguments using their position (index) or their name:

    ```ma
    >>> arguments = Arguments(Argument("hello"))
    >>> arguments[0] is arguments["hello"]
    True
    ```
    """

    def __init__(self, *arguments: Argument) -> None:
        """Initialize the arguments container.

        Parameters:
            *arguments: The initial arguments to add to the container.
        """
        self._args: list[Argument] = list(arguments)

    def __repr__(self) -> str:
        return f"Arguments({', '.join(repr(arg) for arg in self._args)})"

    def __getitem__(self, name_or_index: int | str) -> Argument:
        """Get a argument by index or name."""
        if isinstance(name_or_index, int):
            return self._args[name_or_index]
        name: str = name_or_index.lstrip("*")
        try:
            return next(arg for arg in self._args if arg.name == name)
        except StopIteration as error:
            raise KeyError(f"argument {name_or_index} not found") from error

    def __setitem__(self, name_or_index: int | str, argument: Argument) -> None:
        """Set a argument by index or name."""
        if isinstance(name_or_index, int):
            self._args[name_or_index] = argument
        else:
            name = name_or_index.lstrip("*")
            try:
                index = next(idx for idx, arg in enumerate(self._args) if arg.name == name)
            except StopIteration:
                self._args.append(argument)
            else:
                self._args[index] = argument

    def __delitem__(self, name_or_index: int | str) -> None:
        """Delete a argument by index or name."""
        if isinstance(name_or_index, int):
            del self._args[name_or_index]
        else:
            name: str = name_or_index.lstrip("*")
            try:
                index: int = next(idx for idx, arg in enumerate(self._args) if arg.name == name)
            except StopIteration as error:
                raise KeyError(f"argument {name_or_index} not found") from error
            del self._args[index]

    def __len__(self):
        """The number of arguments."""
        return len(self._args)

    def __iter__(self):
        """Iterate over the arguments, in order."""
        return iter(self._args)

    def __contains__(self, arg_name: str):
        """Whether a argument with the given name is present."""
        try:
            next(arg for arg in self._args if arg.name == arg_name.lstrip("*"))
        except StopIteration:
            return False
        return True

    def add(self, argument: Argument) -> None:
        """Add a argument to the container.

        Parameters:
            argument: The function argument to add.

        Raises:
            ValueError: When a argument with the same name is already present.
        """
        if argument.name in self:
            raise ValueError(f"argument {argument.name} already present")
        self._args.append(argument)


class Object(ObjectAliasMixin):
    """An abstract class representing a Python object."""

    kind: Kind
    """The object kind."""
    is_alias: bool = False
    """Always false for objects."""
    is_collection: bool = False
    """Always false for objects."""
    inherited: bool = False
    """Always false for objects.

    Only aliases can be marked as inherited.
    """

    def __init__(
        self,
        name: str,
        *,
        lineno: int | None = None,
        endlineno: int | None = None,
        docstring: Docstring | None = None,
        node: Node | None = None,
        parent: Object | None = None,
        paths_collection: "PathsCollection | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the object.

        Parameters:
            name: The object name, as declared in the code.
            lineno: The object starting line, or None for modules. Lines start at 1.
            endlineno: The object ending line (inclusive), or None for modules.
            runtime: Whether this object is present at runtime or not.
            docstring: The object docstring.
            parent: The object parent.
            lines_collection: A collection of source code lines.
            paths_collection: A collection of path objects.
        """
        self.name: str = name
        """The object name."""

        self.lineno: int | None = lineno
        """The starting line number of the object."""

        self.endlineno: int | None = endlineno
        """The ending line number of the object."""

        self.docstring: Docstring | None = docstring
        """The object docstring."""

        self.parent: Object | None = parent
        """The parent of the object (none if top module)."""

        self.node: Node | None = node
        """The tree-sitter node of the object."""

        self.members: dict[str, Object | Alias] = {}
        """The object members (folders, namespaces, classes, functions, scripts, properies)."""

        self.attributes: set[str] = set()
        """The object attributes (`Access`, `Hidden`, etc.)."""

        self.aliases: dict[str, Alias] = {}
        """The aliases pointing to this object."""

        self.public: bool | None = None
        """Whether this object is public."""

        self._inherited_members: dict[str, Alias] = {}
        self._paths_collection: "PathsCollection | None" = paths_collection

        # Attach the docstring to this object.
        if docstring:
            docstring.parent = self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self.lineno!r}, {self.endlineno!r})"

    def __bool__(self) -> bool:
        """An object is always true-ish."""
        return True

    def __len__(self) -> int:
        """The number of members in this object, recursively."""
        return len(self.members) + sum(len(member) for member in self.members.values())

    @property
    def has_docstring(self) -> bool:
        """Whether this object has a docstring (empty or not)."""
        return bool(self.docstring)

    def is_kind(self, kind: str | Kind | set[str | Kind]) -> bool:
        """Tell if this object is of the given kind.

        Parameters:
            kind: An instance or set of kinds (strings or enumerations).

        Raises:
            ValueError: When an empty set is given as argument.

        Returns:
            True or False.
        """
        if isinstance(kind, set):
            if not kind:
                raise ValueError("kind must not be an empty set")
            return self.kind in (knd if isinstance(knd, Kind) else Kind(knd) for knd in kind)
        if isinstance(kind, str):
            kind = Kind(kind)
        return self.kind is kind

    @property
    def inherited_members(self) -> dict[str, Alias]:
        """Retrieve a dictionary of inherited members from base classes.

        This method iterates over the base classes in reverse order, resolves their models,
        and collects members that are not already present in the current object's members.

        Returns:
            dict[str, Object]: A dictionary where the keys are member names and the values are the corresponding Object instances.
        """
        return {}

    @property
    def is_namespace(self) -> bool:
        """Whether this object is a namespace."""
        return self.kind is Kind.NAMESPACE

    @property
    def is_folder(self) -> bool:
        """Whether this object is a folder."""
        return self.kind is Kind.FOLDER

    @property
    def is_class(self) -> bool:
        """Whether this object is a class."""
        return self.kind is Kind.CLASS

    @property
    def is_function(self) -> bool:
        """Whether this object is a function."""
        return self.kind is Kind.FUNCTION

    @property
    def is_script(self) -> bool:
        """Whether this object is a script."""
        return self.kind is Kind.SCRIPT

    @property
    def is_property(self) -> bool:
        """Whether this object is a property."""
        return self.kind is Kind.PROPERTY

    def has_attributes(self, *attributes: str) -> bool:
        """Tell if this object has all the given attributes.

        See also: [`labels`][maxx.objects.Object.labels].

        Parameters:
            *attributes: Attributes that must be present.

        Returns:
            True or False.
        """
        return set(attributes).issubset(self.attributes)

    def filter_members(
        self, *predicates: Callable[[Object | Alias], bool]
    ) -> dict[str, Object | Alias]:
        """Filter and return members based on predicates.

        See also: [`members`][maxx.objects.Object.members].

        Parameters:
            *predicates: A list of predicates, i.e. callables accepting a member as argument and returning a boolean.

        Returns:
            A dictionary of members.
        """
        if not predicates:
            return self.members
        members: dict[str, Object | Alias] = {
            name: member
            for name, member in self.members.items()
            if all(predicate(member) for predicate in predicates)
        }
        return members

    @property
    def namespace(self) -> Namespace:
        """The parent namespace of this object.

        See also: [`namespace`][maxx.objects.Namepace].

        Raises:
            ValueError: When the object is not a namespace and does not have a parent.
        """
        if isinstance(self, Namespace):
            return self
        if self.parent is not None:
            return self.parent.namespace
        raise ValueError(f"Object {self.name} does not have a parent module")

    @property
    def path(self) -> str:
        """The dotted path of this object.

        On regular objects (not aliases), the path is the canonical path.

        See also: [`canonical_path`][maxx.objects.Object.canonical_path].
        """
        return self.canonical_path

    @property
    def canonical_path(self) -> str:
        """The full dotted path of this object.

        The canonical path is the path where the object was defined (not imported).

        See also: [`path`][maxx.objects.Object.path].
        """
        if self.parent is None:
            return self.name
        return f"{self.parent.canonical_path}.{self.name}"

    @property
    def paths_collection(self) -> "PathsCollection":
        """The paths collection attached to this object or its parents.

        Raises:
            ValueError: When no paths collection can be found in the object or its parents.
        """
        if self._paths_collection is not None:
            return self._paths_collection
        if self.parent is None:
            raise ValueError("no modules collection in this object or its parents")
        return self.parent.paths_collection

    @property
    def lines_collection(self) -> "LinesCollection":
        """The lines collection attached to this object or its parents.

        See also: [`lines`][maxx.objects.Object.lines],
        [`source`][maxx.objects.Object.source].

        Raises:
            ValueError: When no modules collection can be found in the object or its parents.
        """
        if self._paths_collection is not None:
            return self._paths_collection.lines_collection
        if self.parent is None:
            raise ValueError("no lines collection in this object or its parents")
        return self.parent.lines_collection

    @property
    def filepath(self) -> Path:
        """The file path where this object was defined."""
        if isinstance(self, PathMixin):
            filepath = self._filepath
            if filepath is not None:
                return filepath
        if self.parent is not None:
            return self.parent.filepath
        raise FilePathError(self.name)

    @property
    def lines(self) -> list[str]:
        """The lines containing the source of this object.

        See also: [`lines_collection`][maxx.objects.Object.lines_collection],
        [`source`][maxx.objects.Object.source].
        """

        try:
            lines = self.lines_collection[self.filepath]
        except KeyError:
            return []
        if self.is_namespace:
            return lines
        if self.lineno is None or self.endlineno is None:
            return []
        return lines[self.lineno - 1 : self.endlineno]

    @property
    def source(self) -> str:
        """The source code of this object.

        See also: [`lines`][maxx.objects.Object.lines],
        [`lines_collection`][maxx.objects.Object.lines_collection].
        """
        return dedent("\n".join(self.lines))

    def resolve(self, name: str) -> str:
        """Resolve a name within this object's and parents' scope.

        Parameters:
            name: The name to resolve.

        Raises:
            NameResolutionError: When the name could not be resolved.

        Returns:
            The resolved name.
        """

        # Name is a member this object.
        if name in self.members:
            member = self.members[name]
            if isinstance(member, Alias):
                return member.target_path
            return member.path

        # Name unknown and no more parent scope, could be a built-in.
        if self.parent is None or not self.parent.is_namespace or not self.parent.is_folder:
            raise NameResolutionError(f"{name} could not be resolved in the scope of {self.path}")

        # Recurse in parent.
        return self.parent.resolve(name)


class Alias(ObjectAliasMixin):
    """This class represents an alias, or indirection, to an object declared in another module.

    Aliases represent objects that are in the scope of a module or class,
    but were imported from another module.

    They behave almost exactly like regular objects, to a few exceptions:

    - line numbers are those of the alias, not the target
    - the path is the alias path, not the canonical one
    - the name can be different from the target's
    - if the target can be resolved, the kind is the target's kind
    - if the target cannot be resolved, the kind becomes [Kind.ALIAS][griffe.Kind]
    """

    is_alias: bool = True
    """Always true for aliases."""
    is_collection: bool = False
    """Always false for aliases."""

    def __init__(
        self,
        name: str,
        target: Callable | ObjectAliasMixin,
        *,
        parent: Namespace | Folder | Class | Alias | None = None,
        inherited: bool = False,
    ) -> None:
        """Initialize the alias.

        Parameters:
            name: The alias name.
            target: If it's a string, the target resolution is delayed until accessing the target property.
                If it's an object, or even another alias, the target is immediately set.
            lineno: The alias starting line number.
            endlineno: The alias ending line number.
            runtime: Whether this alias is present at runtime or not.
            parent: The alias parent.
            inherited: Whether this alias wraps an inherited member.
        """
        self.name: str = name
        """The alias name."""

        self.inherited: bool = inherited
        """Whether this alias represents an inherited member."""

        self.public: bool | None = None
        """Whether this alias is public."""

        self.deprecated: str | bool | None = None
        """Whether this alias is deprecated (boolean or deprecation message)."""

        self._parent: Namespace | Folder | Class | Alias | None = parent

        self.target_path: str
        """The path of this alias' target."""

        if callable(target):
            self._target: ObjectAliasMixin | None = None
            self._constructor: Callable = target
            self._lock = threading.Lock()
        else:
            self._target = target
            # Safely get the path attribute if it exists, else set to None
            self.target_path = getattr(target, "path", "")
            self._update_target_aliases()

    def _update_target_aliases(self) -> None:
        with suppress(AttributeError, CyclicAliasError):
            self.target.aliases[self.path] = self

    @property
    def resolved(self) -> bool:
        """Whether this alias' target is resolved."""
        return self._target is not None

    @property
    def _actual(self) -> Object:
        if not self.resolved:
            with self._lock:
                if not self.resolved:
                    self._target = self._constructor()
                paths_seen: dict[str, None] = {}
        target = self._target
        if target is None:
            raise ValueError(f"target of {self.name} is None")
        # Using a dict as an ordered set.
        paths_seen = {}
        while isinstance(target, Alias):
            if target.path in paths_seen:
                raise CyclicAliasError([*paths_seen, target.path])
            paths_seen[target.path] = None
            target = target.target
        return cast(Object, target)

    @property
    def target(self) -> Object:
        """The resolved target (actual object), if possible.

        Upon accessing this property, if the target is not already resolved,
        a lookup is done using the paths collection to find the target.
        """
        return self._actual

    @target.setter
    def target(self, value: Object | Alias) -> None:
        if value is self or value.path == self.path:
            raise CyclicAliasError([self.target_path])
        self._target = value
        self.target_path = value.path
        if self.parent is not None:
            self._target.aliases[self.path] = self

    def __getattr__(self, item):
        return getattr(self._actual, item)

    def __bool__(self) -> bool:
        """An alias is always true-ish."""
        return True

    def __repr__(self) -> str:
        if self.resolved:
            return repr(self._actual)
        return f"Alias({self.name!r}, {self.target_path!r})"

    def __str__(self):
        return str(self._actual)

    def __eq__(self, other):
        return self._actual == other

    def __len__(self):
        return len(self._actual)

    def __getitem__(self, key):
        return self._actual[key]

    @property
    def members(self) -> dict[str, Object | Alias]:
        """The target's members (namespaces, classes, functions, scripts, properties)."""
        # We recreate aliases to maintain a correct hierarchy,
        # and therefore correct paths. The path of an alias member
        # should be the path of the alias plus the member's name,
        # not the original member's path.
        return {
            name: Alias(name, target=member, parent=self, inherited=False)
            for name, member in self._actual.members.items()
        }

    @property
    def inherited_members(self) -> dict[str, Alias]:
        """Members that are inherited from base classes.

        Each inherited member of the target will be wrapped in an alias,
        to preserve correct object access paths.
        """
        # We recreate aliases to maintain a correct hierarchy,
        # and therefore correct paths. The path of an alias member
        # should be the path of the alias plus the member's name,
        # not the original member's path.
        return {
            name: Alias(name, target=member, parent=self, inherited=True)
            for name, member in self._actual.inherited_members.items()
        }


class Folder(PathMixin, Object):
    """The class representing a folder containing MATLAB objects."""

    kind: Kind = Kind.FOLDER

    def __repr__(self) -> str:
        return f"Folder({self.path!r})"

    @property
    def is_folder(self) -> bool:
        return True


class Namespace(PathMixin, Object):
    """The class representing a MATALB namespace."""

    kind: Kind = Kind.NAMESPACE

    def __repr__(self) -> str:
        return f"Namespace({self.path!r})"

    @property
    def is_namespace(self) -> bool:
        """Whether this object is a namespace."""
        return True

    @property
    def is_subnamespace(self) -> bool:
        """Whether this namespace is a subnamespace."""
        return self.parent is not None and self.parent.is_namespace

    @property
    def path(self) -> str:
        """The dotted path of this object.

        On regular objects (not aliases), the path is the canonical path.

        See also: [`canonical_path`][maxx.objects.Object.canonical_path].
        """
        return "+" + self.canonical_path


class Class(PathMixin, Object):
    kind: Kind = Kind.CLASS

    def __init__(
        self,
        *args: Any,
        bases: Sequence[str] | None = None,
        Abstract: bool = False,
        Hidden: bool = False,
        Sealed: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the class.

        Parameters:
            *args: See [`griffe.Object`][].
            bases: The list of base classes, if any.
            decorators: The class decorators, if any.
            **kwargs: See [`griffe.Object`][].
        """
        super().__init__(*args, **kwargs)

        self.bases: list[str] = list(bases) if bases else []
        """The class bases."""

        self.Abstract: bool = Abstract
        self.Hidden: bool = Hidden
        self.Sealed: bool = Sealed

    @property
    def arguments(self) -> Arguments:
        """The arguments of this class' constructor.

        This property fetches inherited members.
        """
        constructor: Function | None = self.constructor
        if constructor is not None:
            return constructor.arguments
        else:
            return Arguments()

    @property
    def constructor(self) -> Function | None:
        """The constructor of this class, if any.

        This property fetches inherited members,
        and therefore is part of the consumer API:
        do not use when producing Griffe trees!
        """
        for item in self._mro():
            if self.name in item.members:
                constructor = item.members[self.name]
                if isinstance(constructor, Function):
                    return constructor
        return None

    @property
    def resolved_bases(self) -> list[Object]:
        resolved_bases: list[Object] = []
        for base in self.bases:
            try:
                resolved_base = self.paths_collection.get_member(base)
                if isinstance(resolved_base, Alias):
                    resolved_base = resolved_base.target
            except (CyclicAliasError, KeyError):
                logger.debug(
                    "Base class %s is not loaded, or not static, it cannot be resolved", base
                )
            else:
                resolved_bases.append(resolved_base)
        return resolved_bases

    def _mro(self, seen: tuple[str, ...] = ()) -> list[Class]:
        seen = (*seen, self.path)
        bases: list[Class] = [base for base in self.resolved_bases if isinstance(base, Class)]
        if not bases:
            return [self]
        for base in bases:
            if base.path in seen:
                cycle: str = " -> ".join(seen) + f" -> {base.path}"
                raise ValueError(
                    f"Cannot compute C3 linearization, inheritance cycle detected: {cycle}"
                )
        return [self, *c3linear_merge(*[base._mro(seen) for base in bases], bases)]

    def mro(self) -> list[Class]:
        """Return a list of classes in order corresponding to MATLAB's MRO."""
        return self._mro()[1:]  # Remove self.

    @property
    def inherited_members(self) -> dict[str, Alias]:
        """Retrieve a dictionary of inherited members from base classes.

        This method iterates over the base classes in reverse order, resolves their models,
        and collects members that are not already present in the current object's members.

        Returns:
            dict[str, Object]: A dictionary where the keys are member names and the values are the corresponding Object instances.
        """
        # if self._inherited_members is not False:
        #     return self._inherited_members

        inherited_members: dict[str, Alias] = {}
        for model in reversed(self.mro()):
            for name, member in model.all_members.items():
                if name not in self.members:
                    inherited_members[name] = Alias(
                        name, target=member, parent=self, inherited=True
                    )

        self._inherited_members = inherited_members
        return inherited_members


class Enumeration(PathMixin, Object):
    """This class represents a MATLAB enumeration."""

    kind: Kind = Kind.ENUMERATION

    def __init__(
        self,
        *args: Any,
        value: Expr | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.value: Expr | None = value
        """The enumeration superclass value"""

    @property
    def has_docstring(self) -> bool:
        """Whether this object has a docstring (empty or not)."""
        return bool(self.docstring)

    def __str__(self) -> str:
        return f"{self.parent.name}.{self.name}" if self.parent else self.name

    def __eq__(self, value: Enumeration) -> bool:
        """Arguments are equal if all their attributes except `docstring` and `function` are equal."""
        return self.name == value.name and self.parent == value.parent


class Function(PathMixin, Object):
    """The class representing a MATLAB function."""

    kind: Kind = Kind.FUNCTION

    def __init__(
        self,
        *args: Any,
        arguments: Arguments | None = None,
        returns: Arguments | None = None,
        Abstract: bool = False,
        Access: AccessKind = AccessKind.public,
        Hidden: bool = False,
        Sealed: bool = False,
        Static: bool = False,
        setter: bool = False,
        getter: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the function.

        Parameters:
            *args: See [`griffe.Object`][].
            arguments: The function arguments.
            returns: The function return type.
            decorators: The function decorators, if any.
            **kwargs: See [`griffe.Object`][].
        """
        super().__init__(*args, **kwargs)
        self.arguments: Arguments = arguments or Arguments()
        """The function arguments."""
        self.returns: Arguments = returns or Arguments()
        """The function return type type."""
        self.Access: AccessKind = Access
        self.Static: bool = Static
        self.Abstract: bool = Abstract
        self.Sealed: bool = Sealed
        self.Hidden: bool = Hidden
        self.is_setter: bool = setter
        self.is_getter: bool = getter

        for argument in self.arguments:
            argument.function = self
        for output in self.returns:
            output.function = self

    @property
    def is_private(self) -> bool:
        """Whether this function is private."""
        return self.Access != AccessKind.public and self.Access != AccessKind.immutable

    @property
    def is_hidden(self) -> bool:
        """Whether this function is hidden."""
        return self.Hidden or self.is_internal

    @property
    def is_method(self) -> bool:
        """Whether this function is a method."""
        return self.parent is not None and self.parent.is_class

    @property
    def is_constructor_method(self) -> bool:
        """Whether this function is a constructor method."""
        return self.is_method and self.parent is not None and self.name == self.parent.name

    @property
    def attributes(self) -> set[str]:
        attributes = set()
        for attr in ["Abstract", "Hidden", "Sealed", "Static"]:
            if getattr(self, attr):
                attributes.add(attr)
        if self.Access != AccessKind.public:
            attributes.add(f"Access={self.Access.value}")
        return attributes

    @attributes.setter
    def attributes(self, *args):
        pass


class Script(PathMixin, Object):
    """The class representing a MATLAB script."""

    kind: Kind = Kind.SCRIPT


class Property(Validatable, Object):
    """The class representing a MATLAB class property."""

    kind: Kind = Kind.PROPERTY

    def __init__(
        self,
        name: str,
        *args: Any,
        AbortSet: bool = False,
        Abstract: bool = False,
        Constant: bool = False,
        Dependent: bool = False,
        GetObservable: bool = False,
        Hidden: bool = False,
        NonCopyable: bool = False,
        SetObservable: bool = False,
        Transient: bool = False,
        WeakHandle: bool = False,
        Access: AccessKind = AccessKind.public,
        GetAccess: AccessKind = AccessKind.public,
        SetAccess: AccessKind = AccessKind.public,
        **kwargs: Any,
    ) -> None:
        # Explicitly initialize both Validatable and Object
        Validatable.__init__(self, name, *args, **kwargs)
        Object.__init__(self, name, *args, **kwargs)
        self.AbortSet: bool = AbortSet
        self.Abstract: bool = Abstract
        self.Constant: bool = Constant
        self.Dependent: bool = Dependent
        self.GetObservable: bool = GetObservable
        self.Hidden: bool = Hidden
        self.NonCopyable: bool = NonCopyable
        self.SetObservable: bool = SetObservable
        self.Transient: bool = Transient
        self.WeakHandle: bool = WeakHandle
        self.Access = Access
        self.GetAccess: AccessKind = GetAccess
        self.SetAccess: AccessKind = SetAccess
        self.setter: Function | None = None
        self.getter: Function | None = None

    def __repr__(self) -> str:
        if self.parent is None:
            return f"Property(name={self.name!r})"
        return f"Property(name={self.name!r}, class={self.parent.name!r})"

    @property
    def is_private(self) -> bool:
        private = self.Access != AccessKind.public
        get_private = self.GetAccess != AccessKind.public
        return private or get_private

    @property
    def attributes(self) -> set[str]:
        attributes = set()
        for attr in [
            "AbortSet",
            "Abstract",
            "Constant",
            "Dependent",
            "GetObservable",
            "Hidden",
            "NonCopyable",
            "SetObservable",
            "Transient",
            "WeakHandle",
        ]:
            if getattr(self, attr):
                attributes.add(attr)
        for attr in ["Access", "GetAccess", "SetAccess"]:
            if getattr(self, attr) != AccessKind.public:
                attributes.add(f"{attr}={getattr(self, attr).value}")
        return attributes

    @attributes.setter
    def attributes(self, *args):
        pass

    @property
    def is_hidden(self) -> bool:
        return self.Hidden
