"""Tests for the docstring_before configuration feature."""

import pytest

from maxx.config import ParserConfig
from maxx.objects import Class, Function, Property
from maxx.treesitter import FileParser


class TestDocstringBefore:
    """Test class for docstring_before configuration feature."""

    @pytest.fixture
    def test_file(self, test_files_dir):
        """Path to the test file with comments before definitions."""
        return test_files_dir / "TestDocstringBefore.m"

    def test_properties_docstring_after_default(self, test_file):
        """Test default behavior: comments after properties are used."""
        config = ParserConfig(docstring_before_properties=False)
        class_obj = FileParser(test_file).parse(config=config)

        assert isinstance(class_obj, Class)

        # With default behavior (comment after), comments attach to previous property
        # Comment before Prop1 has no previous property, so Prop1 has no docstring
        prop1 = class_obj.members["Prop1"]
        assert isinstance(prop1, Property)
        # Comment before Prop2 attaches to Prop1 (original behavior)
        assert prop1.docstring is not None
        assert "Another property with docstring before" in prop1.docstring.value

        prop2 = class_obj.members["Prop2"]
        assert isinstance(prop2, Property)
        # No comment after Prop2, so no docstring
        assert prop2.docstring is None

    def test_properties_docstring_before_enabled(self, test_file):
        """Test docstring_before_properties=True: comments before properties are used."""
        config = ParserConfig(docstring_before_properties=True)
        class_obj = FileParser(test_file).parse(config=config)

        assert isinstance(class_obj, Class)

        # With docstring_before enabled, comments before properties should be used
        prop1 = class_obj.members["Prop1"]
        assert isinstance(prop1, Property)
        assert prop1.docstring is not None
        assert "Property with docstring before" in prop1.docstring.value

        prop2 = class_obj.members["Prop2"]
        assert isinstance(prop2, Property)
        assert prop2.docstring is not None
        assert "Another property with docstring before" in prop2.docstring.value

    def test_arguments_docstring_after_default(self, test_file):
        """Test default behavior: comments after arguments are used."""
        config = ParserConfig(docstring_before_arguments=False)
        class_obj = FileParser(test_file).parse(config=config)

        constructor = class_obj.members["TestDocstringBefore"]
        assert isinstance(constructor, Function)

        # With default behavior, comments attach to previous argument
        # Comment before arg1 has no previous argument, so arg1 has no docstring
        arg1 = constructor.arguments["arg1"]
        assert arg1.docstring is not None
        assert "Second argument docstring" in arg1.docstring.value

        # Comment before arg2 attaches to arg1, so arg2 has no docstring
        arg2 = constructor.arguments["arg2"]
        assert arg2.docstring is None

    def test_arguments_docstring_before_enabled(self, test_file):
        """Test docstring_before_arguments=True: comments before arguments are used."""
        config = ParserConfig(docstring_before_arguments=True)
        class_obj = FileParser(test_file).parse(config=config)

        constructor = class_obj.members["TestDocstringBefore"]
        assert isinstance(constructor, Function)

        # With docstring_before enabled, comments before arguments should be used
        arg1 = constructor.arguments["arg1"]
        assert arg1.docstring is not None
        assert "First argument docstring" in arg1.docstring.value

        arg2 = constructor.arguments["arg2"]
        assert arg2.docstring is not None
        assert "Second argument docstring" in arg2.docstring.value
