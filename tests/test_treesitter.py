"""Tests for the treesitter module."""

import pytest

from maxx.enums import AccessKind, ArgumentKind
from maxx.objects import Class, Enumeration, Function, Script
from maxx.treesitter import FileParser


class MyClassParser:
    """Test class for parsing MATLAB class files."""

    @pytest.fixture(autouse=True)
    def setup(self, test_files_dir):
        """Set up the test by parsing the MyClass.m file."""
        class_file = test_files_dir / "MyClass.m"
        self.class_obj = FileParser(class_file).parse()
        enum_file = test_files_dir / "MyEnum.m"
        self.enum_obj = FileParser(enum_file).parse()

    def test_class_basic_properties(self):
        """Test basic class properties were parsed correctly."""
        assert isinstance(self.class_obj, Class)
        assert self.class_obj.name == "MyClass"

        # Verify docstring was parsed
        assert self.class_obj.docstring is not None
        assert "Test class for MATLAB parser" in self.class_obj.docstring.value
        assert "This class is used to test" in self.class_obj.docstring.value

        # Verify class documentation structure
        assert "Properties:" in self.class_obj.docstring.value
        assert "Methods:" in self.class_obj.docstring.value

    def test_class_enumeration(self):
        """Test that class enumerations were parsed correctly."""
        assert "foo" in self.enum_obj.members
        assert "bar" in self.enum_obj.members
        assert "baz" in self.enum_obj.members

        assert isinstance(self.enum_obj.members["foo"], Enumeration)
        assert isinstance(self.enum_obj.members["bar"], Enumeration)
        assert isinstance(self.enum_obj.members["baz"], Enumeration)

        assert str(self.enum_obj.members["foo"].value) == "0"
        assert str(self.enum_obj.members["bar"].value) == "42"
        assert str(self.enum_obj.members["baz"].value) == "69"

        assert self.enum_obj.members["foo"].docstring is not None
        assert self.enum_obj.members["foo"].docstring.value == "foo"
        assert self.enum_obj.members["bar"].docstring is not None
        assert self.enum_obj.members["bar"].docstring.value == "bar"
        assert self.enum_obj.members["baz"].docstring is None

    def test_class_inheritance(self):
        """Test that class inheritance was parsed correctly."""
        assert len(self.class_obj.bases) == 1
        assert "handle" in self.class_obj.bases

    def test_class_properties(self):
        """Test that class properties were parsed correctly."""
        # Check if properties exist
        assert "Property1" in self.class_obj.members
        assert "Property2" in self.class_obj.members

        # Test Property1 details
        prop1 = self.class_obj.members["Property1"]
        assert str(prop1.type) == "double"
        assert str(prop1.default) == "0"

        # Test Property2 details
        prop2 = self.class_obj.members["Property2"]
        assert str(prop2.type) == "string"
        assert str(prop2.default) == '""'

    def test_constructor_method(self):
        """Test that constructor method was parsed correctly."""
        assert self.class_obj.name in self.class_obj.members
        constructor = self.class_obj.members[self.class_obj.name]

        # Verify it's a Function
        assert isinstance(constructor, Function)

        # Check constructor arguments
        assert constructor.arguments is not None
        assert len(constructor.arguments) == 1

        # Check argument details (excluding obj which is always first for non-static methods)
        init_val = constructor.arguments[0]
        assert init_val.name == "init_val"
        assert str(init_val.type) == "double"
        assert "mustBeNumeric" in str(init_val.validators)
        assert str(init_val.default) == "0"

        # Check docstring
        assert init_val.docstring is not None
        assert "Initial value for Property1" in init_val.docstring.value

        # Check constructor docstring
        assert constructor.docstring is not None
        assert "MyClass constructor" in constructor.docstring.value
        assert "Initialize the class properties" in constructor.docstring.value

    def test_method1(self):
        """Test that method1 was parsed correctly."""
        assert "method1" in self.class_obj.members
        method1 = self.class_obj.members["method1"]

        # Verify it's a Function
        assert isinstance(method1, Function)

        # Verify method has public access by default
        assert method1.Access == AccessKind.public

        # Check method arguments
        assert method1.arguments is not None
        assert len(method1.arguments) == 1  # After removing obj

        # Check input1 argument details
        input1 = method1.arguments[0]  # index 1 because obj is at index 0
        assert input1.name == "input1"
        assert str(input1.type) == "double"
        assert "mustBeNumeric" in str(input1.validators)
        assert input1.dimensions is not None
        assert "1" in input1.dimensions and ":" in input1.dimensions  # Check for (1,:) dimension

        # Check input1 docstring
        assert input1.docstring is not None
        assert "The input parameter for method1" in input1.docstring.value

        # Check method returns
        assert method1.returns is not None
        assert len(method1.returns) == 1
        assert method1.returns[0].name == "result"

    def test_private_method2(self):
        """Test that private method2 was parsed correctly."""
        assert "method2" in self.class_obj.members
        method2 = self.class_obj.members["method2"]

        # Verify it's a Function
        assert isinstance(method2, Function)

        # Verify method has private access
        assert method2.Access == AccessKind.private

        # Check method arguments
        assert method2.arguments is not None
        assert len(method2.arguments) >= 2  # obj + at least one option argument

        # Find the options.text argument
        options_text = None
        options_flag = None
        for arg in method2.arguments:
            if arg.name == "text":
                options_text = arg
            elif arg.name == "flag":
                options_flag = arg

        assert options_text is not None
        assert options_flag is not None

        # Check options.text details
        assert str(options_text.type) == "string"
        assert str(options_text.default) == '"Modified"'
        assert options_text.kind == ArgumentKind.keyword_only

        # Check options.flag details
        assert str(options_flag.type) == "logical"
        assert str(options_flag.default) == "false"
        assert options_flag.dimensions is not None
        assert (
            "1" in options_flag.dimensions and "1" in options_flag.dimensions
        )  # Check for (1,1) dimension
        assert options_flag.kind == ArgumentKind.keyword_only

        # Check docstrings
        assert options_text.docstring is not None
        assert "Text to set for Property2" in options_text.docstring.value

        assert options_flag.docstring is not None
        assert "Optional flag parameter" in options_flag.docstring.value

    def test_public_method3(self):
        """Test that explicitly public method3 was parsed correctly."""
        assert "method3" in self.class_obj.members
        method3 = self.class_obj.members["method3"]

        # Verify it's a Function
        assert isinstance(method3, Function)

        # Verify method has public access
        assert method3.Access == AccessKind.public

        # Check method arguments
        assert method3.arguments is not None
        assert len(method3.arguments) == 2

        # Check factor argument
        factor_arg = method3.arguments[0]  # index 1 because obj is at index 0
        assert factor_arg.name == "factor"
        assert str(factor_arg.type) == "double"
        assert "mustBePositive" in str(factor_arg.validators)
        assert str(factor_arg.default) == "1"
        assert factor_arg.dimensions is not None
        assert (
            "1" in factor_arg.dimensions and "1" in factor_arg.dimensions
        )  # Check for (1,1) dimension

        # Find the options.precision argument
        options_precision = None
        for arg in method3.arguments:
            if arg.name == "precision":
                options_precision = arg

        assert options_precision is not None
        assert str(options_precision.type) == "double"
        assert str(options_precision.default) == "2"
        assert options_precision.validators is not None
        assert "mustBeInRange" in str(options_precision.validators)
        assert options_precision.kind == ArgumentKind.keyword_only

        # Check docstrings
        assert factor_arg.docstring is not None
        assert "Scaling factor for the calculation" in factor_arg.docstring.value

        assert options_precision.docstring is not None
        assert "Precision for output rounding" in options_precision.docstring.value

        # Check method returns
        assert method3.returns is not None
        assert len(method3.returns) == 1
        assert method3.returns[0].name == "result"

    def test_method_access_levels(self):
        """Test that method access levels were parsed correctly."""
        # method1 should have default public access
        method1 = self.class_obj.members["method1"]
        assert method1.Access == AccessKind.public
        assert not method1.is_private

        # method2 should have private access
        method2 = self.class_obj.members["method2"]
        assert method2.Access == AccessKind.private
        assert method2.is_private

        # method3 should have explicit public access
        method3 = self.class_obj.members["method3"]
        assert method3.Access == AccessKind.public
        assert not method3.is_private


def test_parse_function(test_files_dir):
    """Test parsing a MATLAB function file."""
    function_file = test_files_dir / "test_function.m"
    parser = FileParser(function_file)
    model = parser.parse()

    # Verify the model is a Function
    assert isinstance(model, Function)
    assert model.name == "test_function"

    # Check function arguments
    assert model.arguments is not None
    assert len(model.arguments) == 3

    # Check argument names
    arguments = {arg.name: arg for arg in model.arguments}
    assert "input1" in arguments
    assert "input2" in arguments
    assert "text" in arguments

    # Check argument types/annotations
    input1_arg = arguments.get("input1")
    assert input1_arg is not None
    assert str(input1_arg.type) == "double"
    assert input1_arg.dimensions is not None
    assert (
        "1" in input1_arg.dimensions and ":" in input1_arg.dimensions
    )  # Check for (1,:) dimension

    input2_arg = arguments.get("input2")
    assert input2_arg is not None
    assert str(input2_arg.type) == "double"
    assert input2_arg.validators is not None
    assert "mustBePositive" in str(input2_arg.validators)
    assert str(input2_arg.default) == "1"

    text_arg = arguments.get("text")
    assert text_arg is not None
    assert str(text_arg.type) == "string"
    assert str(text_arg.default) == '"Test"'

    # Check argument docstrings
    assert input1_arg.docstring is not None
    assert "The first input parameter" in input1_arg.docstring.value
    assert input2_arg.docstring is not None
    assert "The second input parameter" in input2_arg.docstring.value
    assert text_arg.docstring is not None
    assert "Optional text parameter" in text_arg.docstring.value

    # Check function returns
    assert model.returns is not None
    assert len(model.returns) == 1
    assert model.returns[0].name == "result"

    # Verify docstring was parsed
    assert model.docstring is not None
    assert "Test function for MATLAB parser" in model.docstring.value
    assert "This function is used to test" in model.docstring.value


def test_parse_script(test_files_dir):
    """Test parsing a MATLAB script file."""
    script_file = test_files_dir / "my_script.m"
    parser = FileParser(script_file)
    model = parser.parse()

    # Verify the model is a Script
    assert isinstance(model, Script)
    assert model.name == "my_script"

    # Verify docstring was parsed
    assert model.docstring is not None
    assert "Test script for MATLAB parser" in model.docstring.value
