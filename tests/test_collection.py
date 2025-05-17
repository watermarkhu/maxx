"""Tests for the collect module."""

from pathlib import Path

import pytest

from maxx.collection import PathsCollection
from maxx.objects import Class, Function, Script, Namespace, Folder


# Base directory for test files
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestPathsCollection:
    """Test class for the PathsCollection class."""

    @pytest.fixture(autouse=True)
    def setup(self, test_files_dir):
        """Set up the test by initializing a PathsCollection with test files."""
        self.paths_collection = PathsCollection([test_files_dir], recursive=True)
        # Verify the collection has loaded our test files
        assert "TestClass" in self.paths_collection.members
        assert "test_function" in self.paths_collection.members
        assert "test_script" in self.paths_collection.members
        
        # Store references for easier access in tests
        self.test_class = self.paths_collection.get_member("TestClass")
        self.test_function = self.paths_collection.get_member("test_function")
        self.test_script = self.paths_collection.get_member("test_script")

    def test_path_resolution(self):
        """Test that paths are properly resolved in the collection."""
        # Basic member retrieval
        assert self.test_class is not None
        assert isinstance(self.test_class, Class)
        assert self.test_function is not None
        assert isinstance(self.test_function, Function)
        assert self.test_script is not None
        assert isinstance(self.test_script, Script)
        
        # TODO: Add more specific tests for path resolution
        # 1. Test resolution by full path
        # 2. Test resolution by relative path
        # 3. Test resolution of nested members (e.g., Class methods)
        # 4. Test shadowing behavior (when multiple files with same name exist)
        # 5. Test addpath and rm_path functionality
        
    def test_member_access(self):
        """Test that members and their properties can be accessed correctly."""
        # TODO: Add specific tests for member access
        # 1. Test accessing class methods and properties
        # 2. Test accessing function arguments
        # 3. Test accessing nested namespace members if applicable
        # 4. Test that docstrings are properly attached to members
        
    def test_collection_operations(self):
        """Test operations on the collection itself."""
        # TODO: Add tests for collection operations
        # 1. Test adding new paths
        # 2. Test removing paths
        # 3. Test how changes to the collection affect resolution
        # 4. Test how the collection handles changes to the filesystem
        
    def test_lines_collection(self):
        """Test the lines_collection property of PathsCollection."""
        # TODO: Add tests for the lines_collection
        # 1. Test that source lines are available for objects
        # 2. Test that line numbers match expected values
        # 3. Test retrieving source code from objects
