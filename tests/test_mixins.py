"""Tests for the mixins module."""

from pathlib import Path
from typing import cast

import pytest

from maxx.enums import Kind
from maxx.mixins import (
    DelMembersMixin,
    GetMembersMixin,
    ObjectAliasMixin,
    PathMixin,
    SetMembersMixin,
    _get_parts,
)
from maxx.objects import Object


class TestGetParts:
    """Test the _get_parts helper function."""

    def test_get_parts_string(self):
        """Test _get_parts with a string."""
        result = _get_parts("foo.bar.baz")
        assert result == ["foo", "bar", "baz"]

    def test_get_parts_single_string(self):
        """Test _get_parts with a single string."""
        result = _get_parts("foo")
        assert result == ["foo"]

    def test_get_parts_sequence(self):
        """Test _get_parts with a sequence."""
        result = _get_parts(["foo", "bar"])
        assert result == ["foo", "bar"]

    def test_get_parts_empty_string(self):
        """Test _get_parts with an empty string raises ValueError."""
        with pytest.raises(ValueError, match="Empty strings are not supported"):
            _get_parts("")

    def test_get_parts_empty_sequence(self):
        """Test _get_parts with an empty sequence raises ValueError."""
        with pytest.raises(ValueError, match="Empty tuples are not supported"):
            _get_parts([])


class MockObject:
    """A mock object for testing mixins."""

    def __init__(self, name, kind=Kind.CLASS):
        self.name = name
        self.kind = kind
        self.members = {}
        self.inherited_members = {}
        self.parent = None

    @property
    def all_members(self):
        return {**self.members, **self.inherited_members}

    @property
    def is_class(self):
        return self.kind == Kind.CLASS

    @staticmethod
    def cast(*args, **kwargs):
        """A static method to mimic casting behavior."""
        return cast(Object, MockObject(*args, **kwargs))


class TestDelMembersMixin:
    """Test the DelMembersMixin."""

    def test_delitem_single_member(self):
        """Test deleting a single member using []."""

        class TestClass(DelMembersMixin):
            def __init__(self):
                self.members = {"foo": MockObject.cast("foo"), "bar": MockObject.cast("bar")}
                self.inherited_members = {}

        obj = TestClass()
        del obj["foo"]  # type: ignore[misc]
        assert "foo" not in obj.members
        assert "bar" in obj.members

    def test_delitem_inherited_member(self):
        """Test deleting an inherited member using []."""

        class TestClass(DelMembersMixin):
            def __init__(self):
                self.members = {}
                self.inherited_members = {"inherited": MockObject.cast("inherited")}

        obj = TestClass()
        del obj["inherited"]  # type: ignore[misc]
        assert "inherited" not in obj.inherited_members

    def test_delitem_nested_member(self):
        """Test deleting a nested member using []."""

        class TestClass(DelMembersMixin):
            def __init__(self):
                child = MockObject.cast("child")
                child.members = {"nested": MockObject.cast("nested")}
                self.members = {"child": child}
                self.inherited_members = {}
                self.all_members = self.members

        obj = TestClass()
        # Make the child object support __delitem__
        obj.members["child"].__class__ = type(
            "MockObjectWithDel", (MockObject, DelMembersMixin), {}
        )
        del obj["child", "nested"]  # type: ignore[misc]
        assert "nested" not in obj.members["child"].members

    def test_del_member_single(self):
        """Test deleting a single member using del_member method."""

        class TestClass(DelMembersMixin):
            def __init__(self):
                self.members = {"foo": MockObject.cast("foo"), "bar": MockObject.cast("bar")}

        obj = TestClass()
        obj.del_member("foo")
        assert "foo" not in obj.members
        assert "bar" in obj.members

    def test_del_member_nested(self):
        """Test deleting a nested member using del_member method."""

        class TestClass(DelMembersMixin):
            def __init__(self):
                child = MockObject.cast("child")
                child.members = {"nested": MockObject.cast("nested")}
                child.del_member = lambda key: child.members.pop(  # type: ignore[attr-defined]
                    key[0] if isinstance(key, list) else key
                )  # noqa: E501
                self.members = {"child": child}

        obj = TestClass()
        obj.del_member(["child", "nested"])
        assert "nested" not in obj.members["child"].members


class TestGetMembersMixin:
    """Test the GetMembersMixin."""

    def test_getitem_single_member(self):
        """Test getting a single member using []."""

        class TestClass(GetMembersMixin):
            def __init__(self):
                self.members = {"foo": MockObject.cast("foo")}
                self.inherited_members = {}
                self.all_members = self.members

        obj = TestClass()
        result = obj["foo"]
        assert result.name == "foo"

    def test_getitem_nested_member(self):
        """Test getting a nested member using []."""

        class MockObjectWithGet(MockObject, GetMembersMixin):
            pass

        class TestClass(GetMembersMixin):
            def __init__(self):
                child = MockObjectWithGet("child")
                child.members = {"nested": MockObject.cast("nested")}
                child.inherited_members = {}
                self.members = {"child": child}
                self.inherited_members = {}
                self.all_members = self.members

        obj = TestClass()
        result = obj["child", "nested"]
        assert result.name == "nested"

    def test_get_member_single(self):
        """Test getting a single member using get_member method."""

        class TestClass(GetMembersMixin):
            def __init__(self):
                self.members = {"foo": MockObject.cast("foo")}

        obj = TestClass()
        result = obj.get_member("foo")
        assert result.name == "foo"

    def test_get_member_nested(self):
        """Test getting a nested member using get_member method."""

        class TestClass(GetMembersMixin):
            def __init__(self):
                child = MockObject.cast("child")
                nested = MockObject.cast("nested")
                child.members = {"nested": nested}
                child.get_member = lambda key: child.members[  # type: ignore[attr-defined]
                    key[0] if isinstance(key, list) else key
                ]
                self.members = {"child": child}

        obj = TestClass()
        result = obj.get_member(["child", "nested"])
        assert result.name == "nested"


class TestSetMembersMixin:
    """Test the SetMembersMixin."""

    def test_setitem_single_member(self):
        """Test setting a single member using []."""

        class TestClass(SetMembersMixin):
            def __init__(self):
                self.members = {}

        obj = TestClass()
        new_member = MockObject.cast("new")
        obj["new"] = new_member  # type: ignore[index]
        assert "new" in obj.members
        assert obj.members["new"] is new_member
        assert new_member.parent is obj

    def test_setitem_nested_member(self):
        """Test setting a nested member using []."""

        class TestClass(SetMembersMixin):
            def __init__(self):
                child = MockObject.cast("child")
                child.members = {}
                # Make child support __setitem__
                child.__class__ = type("MockObjectWithSet", (MockObject, SetMembersMixin), {})
                self.members = {"child": child}

        obj = TestClass()
        new_member = MockObject.cast("nested")
        obj["child", "nested"] = new_member  # type: ignore[index]
        assert "nested" in obj.members["child"].members

    def test_set_member_single(self):
        """Test setting a single member using set_member method."""

        class TestClass(SetMembersMixin):
            def __init__(self):
                self.members = {}

        obj = TestClass()
        new_member = MockObject.cast("new")
        obj.set_member("new", new_member)  # type: ignore[arg-type]
        assert "new" in obj.members
        assert obj.members["new"] is new_member
        assert new_member.parent is obj

    def test_set_member_nested(self):
        """Test setting a nested member using set_member method."""

        class TestClass(SetMembersMixin):
            def __init__(self):
                child = MockObject.cast("child")
                child.members = {}
                child.set_member = lambda key, value: child.members.__setitem__(  # type: ignore[attr-defined]
                    key[0] if isinstance(key, list) else key, value
                )
                self.members = {"child": child}

        obj = TestClass()
        new_member = MockObject.cast("nested")
        obj.set_member(["child", "nested"], new_member)  # type: ignore[arg-type]
        assert "nested" in obj.members["child"].members


class TestPathMixin:
    """Test the PathMixin."""

    def test_init_with_filepath(self):
        """Test PathMixin initialization with filepath."""

        class TestClass(PathMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.name = "test"

        filepath = Path("/some/path/file.m")
        obj = TestClass(filepath=filepath)
        assert obj._filepath == filepath

    def test_init_without_filepath(self):
        """Test PathMixin initialization without filepath."""

        class TestClass(PathMixin):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.name = "test"

        obj = TestClass()
        assert obj._filepath is None

    def test_repr(self):
        """Test PathMixin __repr__."""

        class TestClass(PathMixin):
            def __init__(self, name):
                super().__init__()
                self.name = name

        obj = TestClass("MyClass")
        assert repr(obj) == "TestClass(MyClass)"

    def test_is_private_true(self):
        """Test is_private when filepath contains 'private'."""

        class TestClass(PathMixin):
            def __init__(self, filepath):
                super().__init__(filepath=filepath)
                self.name = "test"

        obj = TestClass(Path("/some/private/path/file.m"))
        assert obj.is_private is True

    def test_is_private_false(self):
        """Test is_private when filepath doesn't contain 'private'."""

        class TestClass(PathMixin):
            def __init__(self, filepath):
                super().__init__(filepath=filepath)
                self.name = "test"

        obj = TestClass(Path("/some/public/path/file.m"))
        assert obj.is_private is False

    def test_is_private_no_filepath(self):
        """Test is_private when filepath is None."""

        class TestClass(PathMixin):
            def __init__(self):
                super().__init__(filepath=None)
                self.name = "test"

        obj = TestClass()
        assert obj.is_private is False

    def test_is_internal_true(self):
        """Test is_internal when filepath contains '+internal'."""

        class TestClass(PathMixin):
            def __init__(self, filepath):
                super().__init__(filepath=filepath)
                self.name = "test"

        obj = TestClass(Path("/some/+internal/path/file.m"))
        assert obj.is_internal is True

    def test_is_internal_false(self):
        """Test is_internal when filepath doesn't contain '+internal'."""

        class TestClass(PathMixin):
            def __init__(self, filepath):
                super().__init__(filepath=filepath)
                self.name = "test"

        obj = TestClass(Path("/some/public/path/file.m"))
        assert obj.is_internal is False

    def test_is_hidden(self):
        """Test is_hidden returns same as is_internal."""

        class TestClass(PathMixin):
            def __init__(self, filepath):
                super().__init__(filepath=filepath)
                self.name = "test"

        obj = TestClass(Path("/some/+internal/path/file.m"))
        assert obj.is_hidden is True
        assert obj.is_hidden == obj.is_internal

    def test_relative_filepath_none(self):
        """Test relative_filepath when filepath is None."""

        class TestClass(PathMixin):
            def __init__(self):
                super().__init__(filepath=None)
                self.name = "test"

        obj = TestClass()
        assert obj.relative_filepath is None

    def test_relative_filepath_absolute(self):
        """Test relative_filepath returns absolute path when not relative to cwd."""

        class TestClass(PathMixin):
            def __init__(self, filepath):
                super().__init__(filepath=filepath)
                self.name = "test"

        # Use a path that's definitely not relative to cwd
        abs_path = Path("/absolute/path/file.m")
        obj = TestClass(abs_path)
        result = obj.relative_filepath
        assert result == abs_path


class TestObjectAliasMixin:
    """Test the ObjectAliasMixin."""

    def test_all_members_class(self):
        """Test all_members for a class object."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {"foo": MockObject.cast("foo")}
                self.inherited_members = {"bar": MockObject.cast("bar")}
                self.is_class = True

        obj = TestClass()
        all_members = obj.all_members
        assert "foo" in all_members
        assert "bar" in all_members

    def test_all_members_non_class(self):
        """Test all_members for a non-class object."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {"foo": MockObject.cast("foo")}
                self.inherited_members = {"bar": MockObject.cast("bar")}
                self.is_class = False

        obj = TestClass()
        all_members = obj.all_members
        assert "foo" in all_members
        assert "bar" not in all_members
        assert all_members is obj.members

    def test_folders_property(self):
        """Test the folders property."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {
                    "folder1": MockObject.cast("folder1", Kind.FOLDER),
                    "class1": MockObject.cast("class1", Kind.CLASS),
                }
                self.inherited_members = {}
                self.is_class = False

        obj = TestClass()
        folders = obj.folders
        assert "folder1" in folders
        assert "class1" not in folders

    def test_namespaces_property(self):
        """Test the namespaces property."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {
                    "namespace1": MockObject.cast("namespace1", Kind.NAMESPACE),
                    "class1": MockObject.cast("class1", Kind.CLASS),
                }
                self.inherited_members = {}
                self.is_class = False

        obj = TestClass()
        namespaces = obj.namespaces
        assert "namespace1" in namespaces
        assert "class1" not in namespaces

    def test_scripts_property(self):
        """Test the scripts property."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {
                    "script1": MockObject.cast("script1", Kind.SCRIPT),
                    "class1": MockObject.cast("class1", Kind.CLASS),
                }
                self.inherited_members = {}
                self.is_class = False

        obj = TestClass()
        scripts = obj.scripts
        assert "script1" in scripts
        assert "class1" not in scripts

    def test_classes_property(self):
        """Test the classes property."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {
                    "class1": MockObject.cast("class1", Kind.CLASS),
                    "script1": MockObject.cast("script1", Kind.SCRIPT),
                }
                self.inherited_members = {}
                self.is_class = False

        obj = TestClass()
        classes = obj.classes
        assert "class1" in classes
        assert "script1" not in classes

    def test_functions_property(self):
        """Test the functions property."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {
                    "function1": MockObject.cast("function1", Kind.FUNCTION),
                    "class1": MockObject.cast("class1", Kind.CLASS),
                }
                self.inherited_members = {}
                self.is_class = False

        obj = TestClass()
        functions = obj.functions
        assert "function1" in functions
        assert "class1" not in functions

    def test_properties_property(self):
        """Test the properties property."""

        class TestClass(ObjectAliasMixin):
            def __init__(self):
                self.members = {
                    "property1": MockObject.cast("property1", Kind.PROPERTY),
                    "class1": MockObject.cast("class1", Kind.CLASS),
                }
                self.inherited_members = {}
                self.is_class = False

        obj = TestClass()
        properties = obj.properties
        assert "property1" in properties
        assert "class1" not in properties

    def test_enumerations_property(self):
        """Test the enumerations property."""

        # Note: KIND.CLASS and KIND.ENUMERATION have the same value "class"
        # so we use FUNCTION to test the filtering
        class TestClass(ObjectAliasMixin):
            def __init__(self):
                enum_obj = MockObject.cast("enum1", Kind.ENUMERATION)
                function_obj = MockObject.cast("func1", Kind.FUNCTION)
                self.members = {
                    "enum1": enum_obj,
                    "func1": function_obj,
                }
                self.inherited_members = {}
                self.is_class = False

        obj = TestClass()
        enumerations = obj.enumerations
        # Enumerations property uses all_members which for non-class returns members
        # and filters where kind is Kind.ENUMERATION
        assert "enum1" in enumerations
        assert "func1" not in enumerations
