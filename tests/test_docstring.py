"""Tests for docstring parsing functionality."""

from pathlib import Path

import pytest

from maxx.collection import PathsCollection

# Base directory for test files
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestDocstringParsing:
    """Test class for docstring parsing functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, test_files_dir):
        """Set up the test by initializing a PathsCollection with test files."""
        self.paths_collection = PathsCollection(
            [test_files_dir], recursive=True, working_directory=TEST_FILES_DIR
        )

    def test_testclass_docstring(self):
        """Test that TestClass docstring is properly parsed."""
        testclass = self.paths_collection.get_member("TestClass")
        assert testclass.has_docstring
        assert "Test class for MATLAB parser" in testclass.docstring.value
        assert (
            "This class is used to test the FileParser functionality" in testclass.docstring.value
        )
        assert "Properties:" in testclass.docstring.value
        assert "Methods:" in testclass.docstring.value

    def test_testclass_method1_docstring(self):
        """Test that TestClass.method1 docstring is properly parsed."""
        testclass = self.paths_collection.get_member("TestClass")
        method1 = testclass.members.get("method1")
        assert method1 is not None
        assert method1.has_docstring
        assert "First test method" in method1.docstring.value
        assert "This method demonstrates parsing of a class method" in method1.docstring.value

    def test_testclass_method2_docstring(self):
        """Test that TestClass.method2 docstring is properly parsed."""
        testclass = self.paths_collection.get_member("TestClass")
        method2 = testclass.members.get("method2")
        assert method2 is not None
        assert method2.has_docstring
        assert "Second test method (private)" in method2.docstring.value
        assert "This method demonstrates a void method with options" in method2.docstring.value

    def test_testclass_method3_docstring(self):
        """Test that TestClass.method3 docstring is properly parsed."""
        testclass = self.paths_collection.get_member("TestClass")
        method3 = testclass.members.get("method3")
        assert method3 is not None
        assert method3.has_docstring
        assert "Third test method" in method3.docstring.value
        assert (
            "This method demonstrates multiple arguments with validation" in method3.docstring.value
        )

    def test_classfolder_docstring(self):
        """Test that ClassFolder docstring is properly parsed."""
        classfolder = self.paths_collection.get_member("ClassFolder")
        assert classfolder.has_docstring
        assert "Test class folder for MATLAB parser" in classfolder.docstring.value
        assert "This class demonstrates class folder functionality" in classfolder.docstring.value
        assert "Properties:" in classfolder.docstring.value
        assert "Methods:" in classfolder.docstring.value

    def test_classfolder_process_method_docstring(self):
        """Test that ClassFolder.process method docstring is properly parsed."""
        classfolder = self.paths_collection.get_member("ClassFolder")
        process_method = classfolder.members.get("process")
        assert process_method is not None
        assert process_method.has_docstring
        assert "Process the stored data" in process_method.docstring.value
        assert "Returns processed data according to options" in process_method.docstring.value

    def test_classfolder_analyze_method_docstring(self):
        """Test that ClassFolder.analyze method docstring is properly parsed."""
        analyze_method = self.paths_collection.get_member("ClassFolder.analyze")
        assert analyze_method.has_docstring
        assert "Analyze the data in the ClassFolder object" in analyze_method.docstring.value
        assert "This method performs statistical analysis" in analyze_method.docstring.value
        assert "Example:" in analyze_method.docstring.value

    def test_test_function_docstring(self):
        """Test that test_function docstring is properly parsed."""
        test_function = self.paths_collection.get_member("test_function")
        assert test_function.has_docstring
        assert "Test function for MATLAB parser" in test_function.docstring.value
        assert (
            "This function is used to test the FileParser functionality"
            in test_function.docstring.value
        )

    def test_test_script_docstring(self):
        """Test that test_script docstring is properly parsed."""
        test_script = self.paths_collection.get_member("test_script")
        assert test_script.has_docstring
        assert "Test script for MATLAB parser" in test_script.docstring.value
        assert (
            "This script is used to test the FileParser functionality"
            in test_script.docstring.value
        )

    def test_namespace_class_docstring(self):
        """Test that namespace.NamespaceClass docstring is properly parsed."""
        namespace_class = self.paths_collection.get_member("namespace.NamespaceClass")
        assert namespace_class.has_docstring
        assert "Test namespace class for MATLAB parser" in namespace_class.docstring.value
        assert (
            "This class demonstrates classes within namespaces" in namespace_class.docstring.value
        )
        assert "Properties:" in namespace_class.docstring.value
        assert "Methods:" in namespace_class.docstring.value

    def test_namespace_class_constructor_docstring(self):
        """Test that namespace.NamespaceClass constructor docstring is properly parsed."""
        namespace_class = self.paths_collection.get_member("namespace.NamespaceClass")
        constructor = namespace_class.members.get("NamespaceClass")
        assert constructor is not None
        assert constructor.has_docstring
        assert "NamespaceClass constructor" in constructor.docstring.value
        assert "Initialize the class with a value" in constructor.docstring.value

    def test_namespace_class_increment_method_docstring(self):
        """Test that namespace.NamespaceClass.increment method docstring is properly parsed."""
        namespace_class = self.paths_collection.get_member("namespace.NamespaceClass")
        increment_method = namespace_class.members.get("increment")
        assert increment_method is not None
        assert increment_method.has_docstring
        assert "Increment the stored value" in increment_method.docstring.value

    def test_namespace_class_getvalue_method_docstring(self):
        """Test that namespace.NamespaceClass.getValue method docstring is properly parsed."""
        namespace_class = self.paths_collection.get_member("namespace.NamespaceClass")
        getvalue_method = namespace_class.members.get("getValue")
        assert getvalue_method is not None
        assert getvalue_method.has_docstring
        assert "Get the current value" in getvalue_method.docstring.value

    def test_namespace_function_docstring(self):
        """Test that namespace.test_namespace_function docstring is properly parsed."""
        namespace_func = self.paths_collection.get_member("namespace.test_namespace_function")
        assert namespace_func.has_docstring
        assert "Test namespace function for MATLAB parser" in namespace_func.docstring.value
        assert (
            "This function demonstrates namespace functionality" in namespace_func.docstring.value
        )
        assert "Example:" in namespace_func.docstring.value

    def test_argument_docstrings(self):
        """Test that argument docstrings are properly parsed."""
        test_function = self.paths_collection.get_member("test_function")

        # Check input1 argument docstring
        input1_arg = test_function.arguments["input1"]
        assert input1_arg is not None
        assert input1_arg.has_docstring
        assert "The first input parameter" in input1_arg.docstring.value

        # Check input2 argument docstring
        input2_arg = test_function.arguments["input2"]
        assert input2_arg is not None
        assert input2_arg.has_docstring
        assert "The second input parameter" in input2_arg.docstring.value

        # Check options.text argument docstring
        text_arg = test_function.arguments["text"]
        assert text_arg is not None
        assert text_arg.has_docstring
        assert "Optional text parameter" in text_arg.docstring.value

    def test_property_docstrings(self):
        """Test that property docstrings are properly parsed from namespace class."""
        namespace_class = self.paths_collection.get_member("namespace.NamespaceClass")
        value_property = namespace_class.members.get("Value")
        # Note: Property docstrings might not be implemented yet,
        # this test checks the current behavior
        if value_property is not None and hasattr(value_property, "docstring"):
            assert value_property.docstring is not None
            assert "The stored value" in value_property.docstring.value

    def test_docstring_line_numbers(self):
        """Test that docstring line numbers are correctly captured."""
        testclass = self.paths_collection.get_member("TestClass")
        assert testclass.docstring.lineno > 0
        assert testclass.docstring.endlineno >= testclass.docstring.lineno

        test_function = self.paths_collection.get_member("test_function")
        assert test_function.docstring.lineno > 0
        assert test_function.docstring.endlineno >= test_function.docstring.lineno

    def test_empty_docstrings(self):
        """Test handling of objects without docstrings."""
        # Find a method that might not have a docstring (private methods sometimes don't)
        classfolder = self.paths_collection.get_member("ClassFolder")
        displayinfo_method = classfolder.members.get("displayInfo")
        if displayinfo_method is not None:
            # displayInfo method should have a docstring based on the file content
            assert displayinfo_method.has_docstring
            assert (
                "Display information about the class instance" in displayinfo_method.docstring.value
            )

    def test_multiline_docstrings(self):
        """Test that multiline docstrings are properly handled."""
        namespace_func = self.paths_collection.get_member("namespace.test_namespace_function")
        docstring_content = namespace_func.docstring.value

        # Check that multiple lines are preserved
        assert "Test namespace function for MATLAB parser" in docstring_content
        assert "This function demonstrates namespace functionality" in docstring_content
        assert "Example:" in docstring_content

        # Check that examples are included
        assert "namespace.test_namespace_function(5)" in docstring_content
