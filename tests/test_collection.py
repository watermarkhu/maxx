"""Tests for the collect module."""

from pathlib import Path

import pytest

from maxx.collection import PathsCollection
from maxx.objects import Class, Function, Script

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

    def test_testclass_collection(self):
        """Test that TestClass is properly collected."""
        testclass = self.paths_collection.get_member("TestClass")
        assert isinstance(testclass, Class)
        assert testclass.name == "TestClass"
        assert testclass.filepath.name == "TestClass.m"

    def test_classfolder_collection(self):
        """Test that ClassFolder is properly collected."""
        classfolder = self.paths_collection.get_member("ClassFolder")
        assert isinstance(classfolder, Class)
        assert classfolder.name == "ClassFolder"
        assert classfolder.filepath.name == "ClassFolder.m"

    def test_classfolder_analyze_method(self):
        """Test that ClassFolder.analyze method is properly collected."""
        analyze_method = self.paths_collection.get_member("ClassFolder.analyze")
        assert isinstance(analyze_method, Function)
        assert analyze_method.name == "analyze"
        assert analyze_method.filepath.name == "analyze.m"

    def test_script_collection(self):
        """Test that test_script is properly collected."""
        test_script = self.paths_collection.get_member("test_script")
        assert isinstance(test_script, Script)
        assert test_script.name == "test_script"
        assert test_script.filepath.name == "test_script.m"

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
            "TestClass",
            "ClassFolder",
            "ClassFolder.analyze",
            "test_script",
            "+namespace",
            "namespace.NamespaceClass",
            "namespace.test_namespace_function",
            "test_function",
            "plot_axes",
        }
        assert set(members.keys()) == expected_keys

    def test_getitem_access(self):
        """Test that objects can be accessed using [] syntax."""
        testclass = self.paths_collection["TestClass"]
        assert isinstance(testclass, Class)
        assert testclass.name == "TestClass"

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
