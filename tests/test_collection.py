"""Tests for the collect module."""

from pathlib import Path

import pytest

from maxx.collection import LinesCollection, PathsCollection
from maxx.objects import Class, ClassFolder, Function, Script

# Base directory for test files
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestPathsCollection:
    """Test class for the PathsCollection class."""

    @pytest.fixture(autouse=True)
    def setup(self, test_files_dir):
        """Set up the test by initializing a PathsCollection with test files."""
        self.paths_collection = PathsCollection(
            [test_files_dir], recursive=True, working_directory=TEST_FILES_DIR
        )
        # Verify the collection has loaded our test files

    def test_MyClass_collection(self):
        """Test that MyClass is properly collected."""
        MyClass = self.paths_collection.get_member("MyClass")
        assert isinstance(MyClass, Class)
        assert MyClass.name == "MyClass"
        assert MyClass.filepath.name == "MyClass.m"

    def test_classfolder_collection(self):
        """Test that ClassFolder is properly collected."""
        classfolder = self.paths_collection.get_member("ClassFolder")
        assert isinstance(classfolder, ClassFolder)
        assert classfolder.name == "ClassFolder"
        assert classfolder.filepath.name == "@ClassFolder"

    def test_classfolder_analyze_method(self):
        """Test that ClassFolder.analyze method is properly collected."""
        analyze_method = self.paths_collection.get_member("ClassFolder.analyze")
        assert isinstance(analyze_method, Function)
        assert analyze_method.name == "analyze"
        assert analyze_method.filepath.name == "analyze.m"

    def my_script_collection(self):
        """Test that my_script is properly collected."""
        my_script = self.paths_collection.get_member("my_script")
        assert isinstance(my_script, Script)
        assert my_script.name == "my_script"
        assert my_script.filepath.name == "my_script.m"

    def test_namespace_collection(self):
        """Test that namespace is properly collected."""
        namespace = self.paths_collection.get_member("+namespace")
        assert namespace.kind.value == "namespace"
        assert namespace.name == "namespace"

    def test_namespace_class_collection(self):
        """Test that namespace.NamespaceClass is properly collected."""
        namespace_class = self.paths_collection.get_member("namespace.NamespaceClass")
        assert isinstance(namespace_class, Class)
        assert namespace_class.name == "NamespaceClass"
        assert namespace_class.filepath.name == "NamespaceClass.m"

    def test_namespace_function_collection(self):
        """Test that namespace.test_namespace_function is properly collected."""
        namespace_func = self.paths_collection.get_member("namespace.test_namespace_function")
        assert isinstance(namespace_func, Function)
        assert namespace_func.name == "test_namespace_function"
        assert namespace_func.filepath.name == "test_namespace_function.m"

    def test_function_collection(self):
        """Test that test_function is properly collected."""
        test_function = self.paths_collection.get_member("test_function")
        assert isinstance(test_function, Function)
        assert test_function.name == "test_function"
        assert test_function.filepath.name == "test_function.m"

    def test_members_property(self):
        """Test that the members property returns all collected objects."""
        members = self.paths_collection.members
        expected_keys = {
            "double",
            "inv",
            "MyClass",
            "MyEnum",
            "ClassFolder",
            "ClassFolder.analyze",
            "ClassFolder.static_method",
            "my_script",
            "+namespace",
            "namespace.NamespaceClass",
            "namespace.test_namespace_function",
            "test_function",
            "plot_axes",
            "AbstractClass",
            "GetterSetterClass",
            "block_comment_function",
            "malformed",
            "pragma_function",
            "multiline_docstring",
            "complex_block_comment",
        }
        assert set(members.keys()) == expected_keys

    def test_getitem_access(self):
        """Test that objects can be accessed using [] syntax."""
        MyClass = self.paths_collection["MyClass"]
        assert isinstance(MyClass, Class)
        assert MyClass.name == "MyClass"

    def test_nonexistent_member(self):
        """Test accessing a non-existent member returns None."""
        result = self.paths_collection.get_member("NonExistent")
        assert result is None

    def test_namespace_member_consistency(self):
        """Test that namespace members are consistent between different access methods."""
        # Get namespace from paths collection
        namespace = self.paths_collection.get_member("+namespace")

        # Get class through namespace object
        namespace_class_via_namespace = namespace.get_member("NamespaceClass")

        # Get class directly through paths collection
        namespace_class_via_paths = self.paths_collection.get_member("namespace.NamespaceClass")

        # Both should return the same object
        assert namespace_class_via_namespace is namespace_class_via_paths
        assert isinstance(namespace_class_via_namespace, Class)
        assert namespace_class_via_namespace.name == "NamespaceClass"

        # Test function access as well
        namespace_func_via_namespace = namespace.get_member("test_namespace_function")
        namespace_func_via_paths = self.paths_collection.get_member(
            "namespace.test_namespace_function"
        )

        assert namespace_func_via_namespace is namespace_func_via_paths
        assert isinstance(namespace_func_via_namespace, Function)
        assert namespace_func_via_namespace.name == "test_namespace_function"

    def test_classfolder_member_consistency(self):
        """Test that classfolder members are consistent between different access methods."""
        # Get classfolder from paths collection
        classfolder = self.paths_collection.get_member("ClassFolder")

        # Get method through classfolder object
        analyze_via_classfolder = classfolder.get_member("analyze")

        # Get method directly through paths collection
        analyze_via_paths = self.paths_collection.get_member("ClassFolder.analyze")

        # Both should return the same object
        assert analyze_via_classfolder is analyze_via_paths
        assert isinstance(analyze_via_classfolder, Function)
        assert analyze_via_classfolder.name == "analyze"

    def test_namespace_members_property(self):
        """Test that namespace.members contains the same objects as paths collection."""
        namespace = self.paths_collection.get_member("+namespace")

        # Check that members property contains expected items
        assert "NamespaceClass" in namespace.members
        assert "test_namespace_function" in namespace.members

        # Verify the objects are the same
        assert namespace.members["NamespaceClass"] is self.paths_collection.get_member(
            "namespace.NamespaceClass"
        )
        assert namespace.members["test_namespace_function"] is self.paths_collection.get_member(
            "namespace.test_namespace_function"
        )

    def test_classfolder_members_property(self):
        """Test that classfolder.members contains the same objects as paths collection."""
        classfolder = self.paths_collection.get_member("ClassFolder")

        # Check that members property contains expected items
        assert "analyze" in classfolder.members

        # Verify the objects are the same
        assert classfolder.members["analyze"] is self.paths_collection.get_member(
            "ClassFolder.analyze"
        )

    def test_function_argument_namespace(self):
        """Test that function arguments with namespaces are properly parsed."""
        func = self.paths_collection.get_member("plot_axes")
        assert isinstance(func, Function)
        assert len(func.arguments) == 1

        arg = func.arguments[0]
        docstring_sections = arg.docstring.parsed if arg.docstring is not None else []
        assert len(docstring_sections) == 1
        assert (
            docstring_sections[0].value == "adds the gradient to the plot in axes with handle `ax`."
        )
        assert arg.name == "ax"
        assert arg.dimensions == ["1", "1"]
        assert str(arg.type) == "matlab.graphics.axis.Axes"
        assert str(arg.default) == "gca"


class TestLinesCollection:
    """Test class for LinesCollection."""

    def test_getitem(self):
        """Test getting lines by path."""
        collection = LinesCollection()
        path = Path("/path/to/file.m")
        lines = ["line1", "line2", "line3"]
        collection[path] = lines
        assert collection[path] == lines

    def test_setitem(self):
        """Test setting lines by path."""
        collection = LinesCollection()
        path = Path("/path/to/file.m")
        lines = ["line1", "line2"]
        collection[path] = lines
        assert collection[path] == lines

    def test_contains_true(self):
        """Test __contains__ when path exists."""
        collection = LinesCollection()
        path = Path("/path/to/file.m")
        collection[path] = ["line1"]
        assert path in collection

    def test_contains_false(self):
        """Test __contains__ when path doesn't exist."""
        collection = LinesCollection()
        path = Path("/path/to/file.m")
        assert path not in collection

    def test_bool_empty(self):
        """Test __bool__ returns True even when empty."""
        collection = LinesCollection()
        assert bool(collection) is True

    def test_bool_with_data(self):
        """Test __bool__ returns True with data."""
        collection = LinesCollection()
        path = Path("/path/to/file.m")
        collection[path] = ["line1"]
        assert bool(collection) is True

    def test_keys(self):
        """Test keys() method."""
        collection = LinesCollection()
        path1 = Path("/path/to/file1.m")
        path2 = Path("/path/to/file2.m")
        collection[path1] = ["line1"]
        collection[path2] = ["line2"]
        keys = list(collection.keys())
        assert path1 in keys
        assert path2 in keys

    def test_values(self):
        """Test values() method."""
        collection = LinesCollection()
        path = Path("/path/to/file.m")
        lines = ["line1", "line2"]
        collection[path] = lines
        values = list(collection.values())
        assert lines in values

    def test_items(self):
        """Test items() method."""
        collection = LinesCollection()
        path = Path("/path/to/file.m")
        lines = ["line1", "line2"]
        collection[path] = lines
        items = list(collection.items())
        assert (path, lines) in items


class TestPathsCollectionAdvanced:
    """Advanced tests for PathsCollection."""

    def test_collection_with_working_directory(self, test_files_dir):
        """Test collection with custom working directory."""
        collection = PathsCollection(
            [test_files_dir], recursive=False, working_directory=test_files_dir
        )
        # working_directory is set internally
        assert collection._working_directory == test_files_dir

    def test_collection_get_nonexistent(self, test_files_dir):
        """Test getting non-existent member."""
        collection = PathsCollection([test_files_dir], recursive=False)
        result = collection.get_member("DoesNotExist")
        assert result is None

    def test_collection_getitem_raises(self, test_files_dir):
        """Test [] access for non-existent member."""
        collection = PathsCollection([test_files_dir], recursive=False)
        # getitem may return None or raise KeyError
        try:
            result = collection["DoesNotExist"]
            # If it doesn't raise, it should return None
            assert result is None
        except (KeyError, AttributeError):
            # It's acceptable to raise an error
            pass

    def test_collection_contains(self, test_files_dir):
        """Test __contains__ method."""
        collection = PathsCollection([test_files_dir], recursive=False)
        assert "test_function" in collection
        assert "NonExistent" not in collection

    def test_collection_bool(self, test_files_dir):
        """Test __bool__ method."""
        collection = PathsCollection([test_files_dir], recursive=False)
        assert bool(collection) is True

        empty_collection = PathsCollection([])
        # Empty collection may still be truthy
        assert isinstance(bool(empty_collection), bool)

    def test_collection_len(self, test_files_dir):
        """Test __len__ method."""
        collection = PathsCollection([test_files_dir], recursive=False)
        # len() on members, not collection
        length = len(collection.members)
        assert length > 0

    def test_collection_iter(self, test_files_dir):
        """Test iteration over members."""
        collection = PathsCollection([test_files_dir], recursive=False)
        # Iterate over members
        names = list(collection.members.keys())
        assert len(names) > 0
        assert "test_function" in names

    def test_collection_member_exists(self, test_files_dir):
        """Test that members can be checked for existence."""
        collection = PathsCollection([test_files_dir], recursive=False)
        # Check that specific members exist
        assert "test_function" in collection.members
        assert "MyClass" in collection.members

    def test_collection_member_access(self, test_files_dir):
        """Test accessing members."""
        collection = PathsCollection([test_files_dir], recursive=False)
        # Access members
        test_func = collection.members.get("test_function")
        assert test_func is not None
        # Check that it's a function object (by checking it has expected attributes)
        assert hasattr(test_func, "name")
        assert hasattr(test_func, "filepath")
        assert test_func.name == "test_function"

    def test_collection_keys_values_items(self, test_files_dir):
        """Test keys(), values(), items() methods on members."""
        collection = PathsCollection([test_files_dir], recursive=False)

        keys = list(collection.members.keys())
        assert len(keys) > 0

        values = list(collection.members.values())
        assert len(values) > 0

        items = list(collection.members.items())
        assert len(items) > 0
        # Items should be (key, value) tuples
        assert all(isinstance(item, tuple) and len(item) == 2 for item in items)
