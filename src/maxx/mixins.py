"""This module defines mixins used by Malt."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

from maxx.enums import Kind

if TYPE_CHECKING:
    from maxx.objects import Class, Enumeration, Folder, Function, Namespace, Property, Script


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
            value.parent = self  # ty: ignore[unresolved-attribute]
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
            value.parent = self  # ty: ignore[unresolved-attribute]
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
    def is_private(self) -> bool:
        """Whether this object/alias is private but not special."""
        return any(part == "private" for part in self._filepath.parts) if self._filepath else False

    @property
    def is_internal(self) -> bool:
        return (
            any(part == "+internal" for part in self._filepath.parts) if self._filepath else False
        )

    @property
    def is_hidden(self) -> bool:
        return self.is_internal

    @property
    def relative_filepath(self) -> Path | None:
        """The file path where this object was defined, relative to the current working directory.

        If this object's file path is not relative to the current working directory, return its absolute path.
        """
        cwd = Path.cwd()
        if self._filepath is None:
            return None
        try:
            return self._filepath.relative_to(cwd)
        except ValueError:
            return self._filepath


class ObjectAliasMixin(GetMembersMixin, SetMembersMixin, DelMembersMixin):
    """Mixin class to share methods that appear both in objects and aliases, unchanged.

    Attributes:
        all_members: All members (declared and inherited).
        folder: The folder members.
        namespaces: The namespace members.
        scripts: The script members.
        classes: The class members.
        functions: The function members.
        properties: The property members.
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

    @property
    def enumerations(self) -> "dict[str, Enumeration]":
        return {
            name: member
            for name, member in self.all_members.items()
            if member.kind is Kind.ENUMERATION
        }

    @property
    def is_hidden(self) -> bool:
        return False

    @property
    def is_private(self) -> bool:
        return False
