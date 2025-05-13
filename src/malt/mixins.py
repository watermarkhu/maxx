"""This module defines mixins used by Malt."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence
from pathlib import Path

from malt.enums import Kind

if TYPE_CHECKING:
    from malt.objects import Namespace, Folder, Class, Function, Property, Script


def _get_parts(key: str | Sequence[str]) -> Sequence[str]:
    if isinstance(key, str):
        if not key:
            raise ValueError("Empty strings are not supported")
        parts = key.split(".")
    else:
        parts = list(key)
    if not parts:
        raise ValueError("Empty tuples are not supported")
    return parts


class DelMembersMixin:
    """Mixin class to share methods for deleting members.

    Methods:
        del_member: Delete a member with its name or path.
        __delitem__: Same as `del_member`, with the item syntax `[]`.
    """

    def __delitem__(self, key: str | Sequence[str]) -> None:
        """Delete a member with its name or path.

        Members will be looked up in both declared members and inherited ones,
        triggering computation of the latter.

        Parameters:
            key: The name or path of the member.
        """
        parts = _get_parts(key)
        if len(parts) == 1:
            name = parts[0]
            try:
                del self.members[name]
            except KeyError:
                del self.inherited_members[name]
        else:
            del self.all_members[parts[0]][parts[1:]]

    def del_member(self, key: str | Sequence[str]) -> None:
        """Delete a member with its name or path.

        Members will be looked up in declared members only, not inherited ones.

        Parameters:
            key: The name or path of the member.
        """
        parts = _get_parts(key)
        if len(parts) == 1:
            name = parts[0]
            del self.members[name]
        else:
            self.members[parts[0]].del_member(parts[1:])


class GetMembersMixin:
    """Mixin class to share methods for accessing members.

    Methods:
        get_member: Get a member with its name or path.
        __getitem__: Same as `get_member`, with the item syntax `[]`.
    """

    def __getitem__(self, key: str | Sequence[str]) -> Any:
        """Get a member with its name or path.

        Members will be looked up in both declared members and inherited ones,
        triggering computation of the latter.

        Parameters:
            key: The name or path of the member.
        """
        parts = _get_parts(key)
        if len(parts) == 1:
            return self.all_members[parts[0]]
        return self.all_members[parts[0]][parts[1:]]

    def get_member(self, key: str | Sequence[str]) -> Any:
        """Get a member with its name or path.

        Members will be looked up in declared members only, not inherited ones.

        Parameters:
            key: The name or path of the member.
        """
        parts = _get_parts(key)
        if len(parts) == 1:
            return self.members[parts[0]]
        return self.members[parts[0]].get_member(parts[1:])


class SetMembersMixin:
    """Mixin class to share methods for setting members.

    Methods:
        set_member: Set a member with its name or path.
        __setitem__: Same as `set_member`, with the item syntax `[]`.
    """

    def __setitem__(self, key: str | Sequence[str], value: ObjectAliasMixin) -> None:
        """Set a member with its name or path.

        Parameters:
            key: The name or path of the member.
            value: The member.
        """
        parts = _get_parts(key)
        if len(parts) == 1:
            name = parts[0]
            self.members[name] = value
            value.parent = self
        else:
            self.members[parts[0]][parts[1:]] = value

    def set_member(self, key: str | Sequence[str], value: ObjectAliasMixin) -> None:
        """Set a member with its name or path.

        This method is part of the producer API:
        you can use it safely while building Griffe trees
        (for example in Griffe extensions).

        Parameters:
            key: The name or path of the member.
            value: The member.

        Examples:
            >>> griffe_object.set_member("foo", foo)
            >>> griffe_object.set_member("path.to.bar", bar)
            >>> griffe_object.set_member(("path", "to", "qux"), qux)
        """
        parts = _get_parts(key)
        if len(parts) == 1:
            name = parts[0]
            self.members[name] = value
            value.parent = self
        else:
            self.members[parts[0]].set_member(parts[1:], value)


class PathMixin:
    """
    A mixin class that provides a filepath attribute and related functionality.

    Attributes:
        filepath (Path | None): The file path associated with the object. It can be None if no file path is provided.
    """

    def __init__(self, *args: Any, filepath: Path | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._filepath: Path | None = filepath

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    @property
    def is_internal(self) -> bool:
        return any(part == "+internal" for part in self.filepath.parts) if self.filepath else False

    @property
    def is_hidden(self) -> bool:
        return self.is_internal


class ObjectAliasMixin(GetMembersMixin, SetMembersMixin, DelMembersMixin):
    """Mixin class to share methods that appear both in objects and aliases, unchanged.

    Attributes:
        all_members: All members (declared and inherited).
        modules: The module members.
        classes: The class members.
        functions: The function members.
        attributes: The attribute members.
        is_private: Whether this object/alias is private (starts with `_`) but not special.
        is_class_private: Whether this object/alias is class-private (starts with `__` and is a class member).
        is_special: Whether this object/alias is special ("dunder" attribute/method, starts and end with `__`).
        is_imported: Whether this object/alias was imported from another module.
        is_exported: Whether this object/alias is exported (listed in `__all__`).
        is_wildcard_exposed: Whether this object/alias is exposed to wildcard imports.
        is_public: Whether this object is considered public.
        is_deprecated: Whether this object is deprecated.
    """

    @property
    def all_members(self) -> dict[str, ObjectAliasMixin]:
        """All members (declared and inherited)."""
        if self.is_class:
            return {**self.inherited_members, **self.members}
        return self.members

    @property
    def folders(self) -> "dict[str, Folder]":
        """Thefolder members."""
        return {
            name: member for name, member in self.all_members.items() if member.kind is Kind.FOLDER
        }

    @property
    def namespaces(self) -> "dict[str, Namespace]":
        """The namespace members."""
        return {
            name: member
            for name, member in self.all_members.items()
            if member.kind is Kind.NAMESPACE
        }

    @property
    def scripts(self) -> "dict[str, Script]":
        """The script members."""
        return {name: member for name, member in self.members.items() if member.kind is Kind.SCRIPT}

    @property
    def classes(self) -> "dict[str, Class]":
        """The class members."""
        return {
            name: member for name, member in self.all_members.items() if member.kind is Kind.CLASS
        }

    @property
    def functions(self) -> "dict[str, Function]":
        """The function members."""
        return {
            name: member
            for name, member in self.all_members.items()
            if member.kind is Kind.FUNCTION
        }

    @property
    def properties(self) -> "dict[str, Property]":
        return {
            name: member
            for name, member in self.all_members.items()
            if member.kind is Kind.PROPERTY
        }

    # @property
    # def is_private(self) -> bool:
    #     """Whether this object/alias is private (starts with `_`) but not special."""
    #     return self.name.startswith("_") and not self.is_special

    # @property
    # def is_special(self) -> bool:
    #     """Whether this object/alias is special ("dunder" attribute/method, starts and end with `__`)."""
    #     return self.name.startswith("__") and self.name.endswith("__")

    # @property
    # def is_class_private(self) -> bool:
    #     """Whether this object/alias is class-private (starts with `__` and is a class member)."""
    #     return self.parent and self.parent.is_class and self.name.startswith("__") and not self.name.endswith("__")

    # @property
    # def is_imported(self) -> bool:
    #     """Whether this object/alias was imported from another module."""
    #     return self.parent and self.name in self.parent.imports

    # @property
    # def is_exported(self) -> bool:
    #     """Whether this object/alias is exported (listed in `__all__`)."""
    #     return self.parent.is_module and bool(self.parent.exports and self.name in self.parent.exports)

    # @property
    # def is_wildcard_exposed(self) -> bool:
    #     """Whether this object/alias is exposed to wildcard imports.

    #     To be exposed to wildcard imports, an object/alias must:

    #     - be available at runtime
    #     - have a module as parent
    #     - be listed in `__all__` if `__all__` is defined
    #     - or not be private (having a name starting with an underscore)

    #     Special case for Griffe trees: a submodule is only exposed if its parent imports it.

    #     Returns:
    #         True or False.
    #     """
    #     # If the object is not available at runtime or is not defined at the module level, it is not exposed.
    #     if not self.runtime or not self.parent.is_module:
    #         return False

    #     # If the parent module defines `__all__`, the object is exposed if it is listed in it.
    #     if self.parent.exports is not None:
    #         return self.name in self.parent.exports

    #     # If the object's name starts with an underscore, it is not exposed.
    #     # We don't use `is_private` or `is_special` here to avoid redundant string checks.
    #     if self.name.startswith("_"):
    #         return False

    #     # Special case for Griffe trees: a submodule is only exposed if its parent imports it.
    #     return self.is_alias or not self.is_module or self.is_imported

    # @property
    # def is_public(self) -> bool:
    #     """Whether this object is considered public.

    #     In modules, developers can mark objects as public thanks to the `__all__` variable.
    #     In classes however, there is no convention or standard to do so.

    #     Therefore, to decide whether an object is public, we follow this algorithm:

    #     - If the object's `public` attribute is set (boolean), return its value.
    #     - If the object is listed in its parent's (a module) `__all__` attribute, it is public.
    #     - If the parent (module) defines `__all__` and the object is not listed in, it is private.
    #     - If the object has a private name, it is private.
    #     - If the object was imported from another module, it is private.
    #     - Otherwise, the object is public.
    #     """
    #     # Give priority to the `public` attribute if it is set.
    #     if self.public is not None:
    #         return self.public

    #     # If the object is a module and its name does not start with an underscore, it is public.
    #     # Modules are not subject to the `__all__` convention, only the underscore prefix one.
    #     if not self.is_alias and self.is_module and not self.name.startswith("_"):
    #         return True

    #     # If the object is defined at the module-level and is listed in `__all__`, it is public.
    #     # If the parent module defines `__all__` but does not list the object, it is private.
    #     if self.parent and self.parent.is_module and bool(self.parent.exports):
    #         return self.name in self.parent.exports

    #     # Special objects are always considered public.
    #     # Even if we don't access them directly, they are used through different *public* means
    #     # like instantiating classes (`__init__`), using operators (`__eq__`), etc..
    #     if self.is_private:
    #         return False

    #     # TODO: In a future version, we will support two conventions regarding imports:
    #     # - `from a import x as x` marks `x` as public.
    #     # - `from a import *` marks all wildcard imported objects as public.
    #     if self.is_imported:  # noqa: SIM103
    #         return False

    #     # If we reached this point, the object is public.
    #     return True

    # @property
    # def is_deprecated(self) -> bool:
    #     """Whether this object is deprecated."""
    #     # NOTE: We might want to add more ways to detect deprecations in the future.
    #     return bool(self.deprecated)
