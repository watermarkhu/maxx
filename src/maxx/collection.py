"""Functions and classes for collecting MATLAB objects from paths."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any, ItemsView, KeysView, Sequence, TypeVar, ValuesView

from maxx.objects import (
    Alias,
    Class,
    Docstring,
    Folder,
    Function,
    Namespace,
    Object,
)
from maxx.treesitter import FileParser

MFILE_SUFFIX = ".m"
CLASSFOLDER_PREFIX = "@"
NAMESPACE_PREFIX = "+"
FOLDER_PREFIXES = (CLASSFOLDER_PREFIX, NAMESPACE_PREFIX)
PRIVATE_FOLDER = "private"
CONTENTS_FILE = "Contents.m"


PathType = TypeVar("PathType", bound=Object)

__all__ = ["LinesCollection", "PathsCollection"]


class _PathGlobber:
    """
    A class to recursively glob paths as MATLAB would do it.
    """

    def __init__(self, path: Path, recursive: bool = False):
        self._idx = 0
        self._paths: list[Path] = []
        self._glob(path, recursive)

    def _glob(self, path: Path, recursive: bool = False):
        for member in path.iterdir():
            if (
                member.is_dir()
                and recursive
                and member.name[0] not in FOLDER_PREFIXES
                and member.stem != PRIVATE_FOLDER
            ):
                self._glob(member, recursive=True)
            elif member.is_dir() and member.stem[0] in FOLDER_PREFIXES:
                self._paths.append(member)
                self._glob(member)
            elif (
                member.is_file() and member.suffix == MFILE_SUFFIX and member.name != CONTENTS_FILE
            ):
                self._paths.append(member)

    def max_stem_length(self) -> int:
        return max(len(path.stem) for path in self._paths)

    def __len__(self):
        return len(self._paths)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            item = self._paths[self._idx]
        except IndexError as err:
            raise StopIteration from err
        self._idx += 1
        return item


class _PathResolver:
    """
    A class to lazily collect and object MATLAB objects from a given path.

    Methods:
        is_class_folder: Checks if the path is a class folder.
        is_namespace: Checks if the path is a namespace.
        is_in_namespace: Checks if the path is within a namespace.
        name: Returns the name of the MATLAB object, including namespace if applicable.
        object: Collects and returns the MATLAB object object..
    """

    def __init__(self, path: Path, paths_collection: PathsCollection):
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        self._path: Path = path
        self._object: Object | None = None
        self._paths_collection: PathsCollection = paths_collection

    @property
    def is_folder(self) -> bool:
        return self._path.is_dir() and self._path.name[0] not in FOLDER_PREFIXES

    @property
    def is_class_folder(self) -> bool:
        return self._path.is_dir() and self._path.name[0] == CLASSFOLDER_PREFIX

    @property
    def is_namespace(self) -> bool:
        return self._path.is_dir() and self._path.name[0] == NAMESPACE_PREFIX

    @property
    def is_in_namespace(self) -> bool:
        return self._path.is_dir() and self._path.parent.name[0] == NAMESPACE_PREFIX

    @property
    def name(self):
        if self.is_in_namespace:
            parts = list(self._path.parts)
            item = len(parts) - 2
            nameparts = []
            while item >= 0:
                if parts[item][0] != NAMESPACE_PREFIX:
                    break
                nameparts.append(parts[item][1:])
                item -= 1
            nameparts.reverse()
            namespace = ".".join(nameparts) + "."
        else:
            namespace = ""

        if self.is_class_folder or self.is_namespace:
            name = namespace + self._path.name[1:]
        else:
            name = namespace + self._path.stem

        if self.is_namespace:
            return NAMESPACE_PREFIX + name
        else:
            return name

    def __call__(self) -> Object | None:
        if not self._path.exists():
            raise FileNotFoundError(f"Path does not exist: {self._path}")

        if self._object is None:
            if self.is_class_folder:
                self._object = self._collect_classfolder(self._path)
            elif self.is_namespace:
                self._object = self._collect_namespace(self._path)
            elif self.is_folder:
                self._object = self._collect_folder(self._path)
            else:
                self._object = self._collect_path(self._path)
        if self._object is not None and self.is_in_namespace:
            parent = self._paths_collection._objects[self._path.parent]
            if isinstance(parent, Namespace):
                self._object.parent = parent
            else:
                ValueError("Parent must be a namespace")
        return self._object

    def _collect_path(self, path: Path, **kwargs: Any) -> Object:
        file = FileParser(path, paths_collection=self._paths_collection)
        object = file.parse(paths_collection=self._paths_collection, **kwargs)
        self._paths_collection.lines_collection[path] = file.content.split("\n")
        return object

    def _collect_directory(
        self, path: Path, object: PathType, set_parent: bool = False
    ) -> PathType:
        for item in path.iterdir():
            if item.is_dir() and item.name[0] in FOLDER_PREFIXES:
                if item not in self._paths_collection._objects:
                    raise KeyError(f"Path not found in collection: {item}")
                subobject = self._paths_collection._objects[item].target
                if subobject is not None:
                    object.members[subobject.name] = subobject
                    if set_parent:
                        subobject.parent = object

            elif item.is_file() and item.suffix == MFILE_SUFFIX:
                if item.name == CONTENTS_FILE:
                    contentsfile = self._collect_path(item)
                    object.docstring = contentsfile.docstring
                else:
                    if item not in self._paths_collection._objects:
                        raise KeyError(f"Path not found in collection: {item}")
                    subobject = self._paths_collection._objects[item].target
                    if subobject is not None:
                        object.members[subobject.name] = subobject
                        if set_parent:
                            subobject.parent = object

        if object.docstring is None:
            object.docstring = self._collect_readme_md(path, object)

        return object

    def _collect_classfolder(self, path: Path) -> Class | None:
        classfile = path / (path.name[1:] + MFILE_SUFFIX)
        if not classfile.exists():
            return None
        object = self._collect_path(classfile)
        if not isinstance(object, Class):
            return None
        for member in path.iterdir():
            if member.is_file() and member.suffix == MFILE_SUFFIX and member != classfile:
                if member.name == CONTENTS_FILE and object.docstring is None:
                    contentsfile = self._collect_path(member)
                    object.docstring = contentsfile.docstring
                else:
                    if member not in self._paths_collection._objects:
                        raise KeyError(f"Path not found in collection: {member}")
                    method = self._paths_collection._objects[member].target
                    if method is not None and isinstance(method, Function):
                        method.parent = object
                        object.members[method.name] = method
        if object.docstring is None:
            object.docstring = self._collect_readme_md(path, object)
        return object

    def _collect_namespace(self, path: Path) -> Namespace:
        name = self.name[1:].split(".")[-1]
        object = Namespace(name, filepath=path, paths_collection=self._paths_collection)
        return self._collect_directory(path, object, set_parent=True)

    def _collect_folder(self, path: Path) -> Folder:
        name = path.stem
        object = Folder("/" + name, filepath=path, paths_collection=self._paths_collection)
        return self._collect_directory(path, object, set_parent=False)

    def _collect_readme_md(self, path, parent: PathType) -> Docstring | None:
        if (path / "README.md").exists():
            readme = path / "README.md"
        elif (path / "readme.md").exists():
            readme = path / "readme.md"
        else:
            return None

        with open(readme, "r") as file:
            content = file.read()
        return Docstring(content, parent=parent)  # type: ignore[arg-type]


class LinesCollection:
    """A simple dictionary containing the modules source code lines."""

    def __init__(self) -> None:
        """Initialize the collection."""
        self._data: dict[Path, list[str]] = {}

    def __getitem__(self, key: Path) -> list[str]:
        """Get the lines of a file path."""
        return self._data[key]

    def __setitem__(self, key: Path, value: list[str]) -> None:
        """Set the lines of a file path."""
        self._data[key] = value

    def __contains__(self, item: Path) -> bool:
        """Check if a file path is in the collection."""
        return item in self._data

    def __bool__(self) -> bool:
        """A lines collection is always true-ish."""
        return True

    def keys(self) -> KeysView:
        """Return the collection keys.

        Returns:
            The collection keys.
        """
        return self._data.keys()

    def values(self) -> ValuesView:
        """Return the collection values.

        Returns:
            The collection values.
        """
        return self._data.values()

    def items(self) -> ItemsView:
        """Return the collection items.

        Returns:
            The collection items.
        """
        return self._data.items()


class PathsCollection:
    """
    PathsCollection is a class that manages a collection of MATLAB paths and their corresponding objects.

    Attributes:
        config (Mapping): Configuration settings for the PathsCollection.
        lines_collection (LinesCollection): An instance of LinesCollection for managing lines.

    Args:
        matlab_path (Sequence[str | Path]): A list of strings or Path objects representing the MATLAB paths.
        recursive (bool, optional): If True, recursively adds all subdirectories of the given paths to the search path. Defaults to False.
        working_directory (Path | None, optional): The path to the configuration file. Defaults to None.

    Methods:
        members() -> dict:
            Returns a dictionary of members with their corresponding objects.

        resolve(identifier: str, config: Mapping = {}) -> Object | None:
            Resolves the given identifier to a object object.

        update_object(object: Object, config: Mapping) -> Object:
            Updates the given object object with the provided configuration.

        addpath(path: str | Path, to_end: bool = False, recursive: bool = False) -> list[Path]:
            Adds a path to the search path.

        rm_path(path: str | Path, recursive: bool = False) -> list[Path]:
            Removes a path from the search path and updates the namespace and database accordingly.

    """

    is_collection = True
    """Marked as collection to distinguish from objects."""

    def __init__(
        self,
        matlab_path: Sequence[str | Path],
        recursive: bool = False,
        working_directory: Path = Path.cwd(),
    ):
        """
        Initialize an instance of PathsCollection.

        Args:
            matlab_path (list[str | Path]): A list of strings or Path objects representing the MATLAB paths.
            recursive (bool): Whether to add the paths recursively
            working_directory: (Path | None)
        Raises:
            TypeError: If any element in matlab_path is not a string or Path object.
        """
        for path in matlab_path:
            if not isinstance(path, (str, Path)):
                raise TypeError(f"Expected str or Path, got {type(path)}")

        self._path: deque[Path] = deque()
        # The matlab path from which objects are resolved.
        self._mapping: dict[str, deque[Path]] = defaultdict(deque)
        # The mapping from an identifier to an callable. This is also a deque since callables can be shadowed.
        self._objects: dict[Path, Alias] = {}
        # The mapping from a path to a object. The lazyModel ensures that the file is parsed only when resolved.
        self._members: dict[Path, list[tuple[str, Path]]] = defaultdict(list)
        # Stores which objects and subpaths are added from each added path. Allows for path element to be removed.
        self._folders: dict[Path, Alias] = {}
        # Stores mapping of each directory to a Folder object. Allows for auto-documenting folders.
        self._working_directory: Path = working_directory
        self.lines_collection = LinesCollection()

        for path in matlab_path:
            self.addpath(Path(path), to_end=True, recursive=recursive)

    @property
    def members(self) -> dict[str, Any]:
        return {identifier: self._objects[paths[0]] for identifier, paths in self._mapping.items()}

    def get_member(self, identifier: str) -> Any:
        return self[identifier]

    def __contains__(self, identifier: str) -> bool:
        """
        Check if the identifier exists in the collection.

        Args:
            identifier (str): The identifier to check.

        Returns:
            bool: True if the identifier exists, False otherwise.
        """
        try:
            return self.__getitem__(identifier) is not None
        except KeyError:
            return False

    def __getitem__(self, identifier: str) -> Any:
        """
        Resolve an identifier to a Object object.

        This method attempts to resolve a given identifier to a corresponding
        Object object using the internal mapping and objects. If the identifier
        is not found directly, it will attempt to resolve it by breaking down the
        identifier into parts and resolving each part recursively.

        Args:
            identifier (str): The identifier to resolve.

        Returns:
            Object or None: The resolved Object object if found, otherwise None.
        """

        # Find in global database
        if identifier in self._mapping:
            alias = self._objects[self._mapping[identifier][0]]
            object = alias.target

        elif "/" in identifier:
            absolute_path = (self._working_directory / Path(identifier)).resolve()
            if absolute_path.exists():
                if absolute_path.suffix:
                    path, member = absolute_path.parent, absolute_path.stem
                else:
                    path, member = absolute_path, None
                folder = self._folders.get(path, None)

                if folder is not None:
                    # Get folder object
                    object = folder.target

                    if isinstance(object, Folder) and member is not None:
                        # Get member from folder
                        item = object.members.get(member, None)
                        if item is not None:
                            if isinstance(item, Alias):
                                object = item.target
                            else:
                                object = item
                        else:
                            object = None
                else:
                    object = None
            else:
                object = None

        else:
            object = None
            name_parts = identifier.split(".")
            if len(name_parts) > 1:
                base = self.get_member(".".join(name_parts[:-1]))
                if base is None or name_parts[-1] not in base.members:
                    object = None
                else:
                    object = base.members[name_parts[-1]]
            else:
                object = None

        if isinstance(object, Alias):
            return object.target
        return object

    def addpath(self, path: str | Path, to_end: bool = False, recursive: bool = False):
        """
        Add a path to the search path.

        Args:
            path (str | Path): The path to be added.
            to_end (bool, optional): Whether to add the path to the end of the search path. Defaults to False.

        Returns:
            list[Path]: The previous search path before adding the new path.
        """
        if isinstance(path, str):
            path = Path(path)

        if path in self._path:
            self._path.remove(path)

        if to_end:
            self._path.append(path)
        else:
            self._path.appendleft(path)

        for member in list(_PathGlobber(path, recursive=recursive)):
            object = Alias(member.stem, target=_PathResolver(member, self))
            self._objects[member] = object

        for member, object in self._objects.items():
            self._mapping[object.path].append(member)
            self._members[path].append((object.name, member))

            if member.parent not in self._folders:
                self._folders[member.parent] = Alias(
                    str(member.parent), target=_PathResolver(member.parent, self)
                )

    def rm_path(self, path: str | Path, recursive: bool = False):
        """
        Removes a path from the search path and updates the namespace and database accordingly.

        Args:
            path (str | Path): The path to be removed from the search path.
            recursive (bool, optional): If True, recursively removes all subdirectories of the given path from the search path. Defaults to False.

        Returns:
            list[Path]: The previous search path before the removal.

        """
        if isinstance(path, str):
            path = Path(path)

        if path not in self._path:
            return list(self._path)

        self._path.remove(path)

        for name, member in self._members.pop(path):
            self._mapping[name].remove(member)
            self._objects.pop(member)

        if recursive:
            for subdir in [item for item in self._path if _is_subdirectory(path, item)]:
                self.rm_path(subdir, recursive=False)


def _is_subdirectory(parent_path: Path, child_path: Path) -> bool:
    """
    Check if a path is a subdirectory of another path.

    Args:
        parent_path: The potential parent directory path.
        child_path: The potential subdirectory path.

    Returns:
        True if child_path is a subdirectory of parent_path, False otherwise.
    """
    try:
        child_path.relative_to(parent_path)
    except ValueError:
        return False
    else:
        return True
