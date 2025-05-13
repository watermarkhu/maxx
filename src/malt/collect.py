"""Functions and classes for collecting MATLAB objects from paths."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Sequence, TypeVar, ItemsView, KeysView, ValuesView

from malt.mixins import ObjectAliasMixin
from malt.objects import (
    Alias,
    Class,
    Docstring,
    Folder,
    Object,
    Namespace,
    PathMixin,
)
from malt.treesitter import FileParser


MFILE_SUFFIX = ".m"
CLASSFOLDER_PREFIX = "@"
NAMESPACE_PREFIX = "+"
FOLDER_PREFIXES = (CLASSFOLDER_PREFIX, NAMESPACE_PREFIX)
PRIVATE_FOLDER = "private"
CONTENTS_FILE = "Contents.m"


PathType = TypeVar("PathType", bound=PathMixin)

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
                and member.stem[0] not in FOLDER_PREFIXES
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
    A class to lazily collect and model MATLAB objects from a given path.

    Methods:
        is_class_folder: Checks if the path is a class folder.
        is_namespace: Checks if the path is a namespace.
        is_in_namespace: Checks if the path is within a namespace.
        name: Returns the name of the MATLAB object, including namespace if applicable.
        model: Collects and returns the MATLAB object model..
    """

    def __init__(self, path: Path, paths_collection: PathsCollection):
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        self._path: Path = path
        self._model: Object | None = None
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

        if self._model is None:
            if self.is_class_folder:
                self._model = self._collect_classfolder(self._path)
            elif self.is_namespace:
                self._model = self._collect_namespace(self._path)
            elif self.is_folder:
                self._model = self._collect_folder(self._path)
            else:
                self._model = self._collect_path(self._path)
        if self._model is not None:
            self._model.parent = self._collect_parent(self._path.parent)
        return self._model

    def _collect_parent(self, path: Path) -> ObjectAliasMixin | None:
        if self.is_in_namespace:
            parent = self._paths_collection._models[path]
        else:
            parent = None
        return parent

    def _collect_path(self, path: Path, **kwargs: Any) -> Object:
        file = FileParser(path, paths_collection=self._paths_collection)
        model = file.parse(paths_collection=self._paths_collection, **kwargs)
        self._paths_collection.lines_collection[path] = file.content.split("\n")
        return model

    def _collect_directory(self, path: Path, model: PathType) -> PathType:
        for item in path.iterdir():
            if item.is_dir() and item.name[0] in FOLDER_PREFIXES:
                if item not in self._paths_collection._models:
                    raise KeyError(f"Path not found in collection: {item}")
                submodel = self._paths_collection._models[item].model()
                if submodel is not None:
                    model.members[submodel.name] = submodel

            elif item.is_file() and item.suffix == MFILE_SUFFIX:
                if item.name == CONTENTS_FILE:
                    contentsfile = self._collect_path(item)
                    model.docstring = contentsfile.docstring
                else:
                    if item not in self._paths_collection._models:
                        raise KeyError(f"Path not found in collection: {item}")
                    submodel = self._paths_collection._models[item].model()
                    if submodel is not None:
                        model.members[submodel.name] = submodel

        if model.docstring is None:
            model.docstring = self._collect_readme_md(path, model)

        return model

    def _collect_classfolder(self, path: Path) -> Class | None:
        classfile = path / (path.name[1:] + MFILE_SUFFIX)
        if not classfile.exists():
            return None
        model = self._collect_path(classfile)
        if not isinstance(model, Class):
            return None
        for member in path.iterdir():
            if member.is_file() and member.suffix == MFILE_SUFFIX and member != classfile:
                if member.name == CONTENTS_FILE and model.docstring is None:
                    contentsfile = self._collect_path(member)
                    model.docstring = contentsfile.docstring
                else:
                    method = self._collect_path(member)
                    method.parent = model
                    model.members[method.name] = method
        if model.docstring is None:
            model.docstring = self._collect_readme_md(path, model)
        return model

    def _collect_namespace(self, path: Path) -> Namespace:
        name = self.name[1:].split(".")[-1]
        model = Namespace(name, filepath=path, paths_collection=self._paths_collection)
        return self._collect_directory(path, model)

    def _collect_folder(self, path: Path) -> Folder:
        name = path.stem
        model = Folder("/" + name, filepath=path, paths_collection=self._paths_collection)
        return self._collect_directory(path, model)

    def _collect_readme_md(self, path, parent: PathMixin) -> Docstring | None:
        if (path / "README.md").exists():
            readme = path / "README.md"
        elif (path / "readme.md").exists():
            readme = path / "readme.md"
        else:
            return None

        with open(readme, "r") as file:
            content = file.read()
        return Docstring(content, parent=parent)


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
    PathsCollection is a class that manages a collection of MATLAB paths and their corresponding models.

    Attributes:
        config (Mapping): Configuration settings for the PathsCollection.
        lines_collection (LinesCollection): An instance of LinesCollection for managing lines.

    Args:
        matlab_path (Sequence[str | Path]): A list of strings or Path objects representing the MATLAB paths.
        recursive (bool, optional): If True, recursively adds all subdirectories of the given paths to the search path. Defaults to False.
        working_directory (Path | None, optional): The path to the configuration file. Defaults to None.

    Methods:
        members() -> dict:
            Returns a dictionary of members with their corresponding models.

        resolve(identifier: str, config: Mapping = {}) -> Object | None:
            Resolves the given identifier to a model object.

        update_model(model: Object, config: Mapping) -> Object:
            Updates the given model object with the provided configuration.

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
        self._models: dict[Path, ObjectAliasMixin] = {}
        # The mapping from a path to a model. The lazyModel ensures that the file is parsed only when resolved.
        self._members: dict[Path, list[tuple[str, Path]]] = defaultdict(list)
        # Stores which models and subpaths are added from each added path. Allows for path element to be removed.
        self._folders: dict[Path, ObjectAliasMixin] = {}
        # Stores mapping of each directory to a Folder object. Allows for auto-documenting folders.
        self._working_directory: Path = working_directory
        self.lines_collection = LinesCollection()

        for path in matlab_path:
            self.addpath(Path(path), to_end=True, recursive=recursive)

    @property
    def members(self) -> dict[str, Any]:
        return {
            identifier: self._models[paths[0]].model()
            for identifier, paths in self._mapping.items()
        }

    def get_member(self, identifier: str) -> Any:
        return self[identifier]

    def __getitem__(self, identifier: str) -> Any:
        """
        Resolve an identifier to a Object model.

        This method attempts to resolve a given identifier to a corresponding
        Object model using the internal mapping and models. If the identifier
        is not found directly, it will attempt to resolve it by breaking down the
        identifier into parts and resolving each part recursively.

        Args:
            identifier (str): The identifier to resolve.

        Returns:
            Object or None: The resolved Object model if found, otherwise None.
        """

        # Find in global database
        if identifier in self._mapping:
            model = self._models[self._mapping[identifier][0]].model()

        elif "/" in identifier:
            absolute_path = (self._working_directory / Path(identifier)).resolve()
            if absolute_path.exists():
                if absolute_path.suffix:
                    path, member = absolute_path.parent, absolute_path.stem
                else:
                    path, member = absolute_path, None
                _PathResolver = self._folders.get(path, None)

                if _PathResolver is not None:
                    # Get folder model
                    model = _PathResolver.model()

                    if isinstance(model, Folder) and member is not None:
                        # Get member from folder
                        model = model.members.get(member, None)
                else:
                    model = None
            else:
                model = None

        else:
            model = None
            name_parts = identifier.split(".")
            if len(name_parts) > 1:
                base = self.get_member(".".join(name_parts[:-1]))
                if base is None or name_parts[-1] not in base.members:
                    model = None
                else:
                    model = base.members[name_parts[-1]]
            else:
                model = None

        if isinstance(model, Object):
            return model
        return None

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

        for member in _PathGlobber(path, recursive=recursive):
            model = Alias(str(member), target=_PathResolver(member, self))
            self._models[member] = model
            self._mapping[model.name].append(member)
            self._members[path].append((model.name, member))

            if model.is_folder:
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
            self._models.pop(member)

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
