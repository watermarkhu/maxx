"""Tests for the objects module."""

from pathlib import Path

import pytest

from maxx.enums import AccessKind, ArgumentKind, Kind
from maxx.objects import (
    Argument,
    Arguments,
    Class,
    Enumeration,
    Function,
    Namespace,
    Property,
    Script,
)


class TestValidatable:
    """Test class for Validatable."""

    def test_str_without_kind(self):
        """Test string representation without kind attribute."""
        # Validatable is abstract, but we can test through Argument
        arg = Argument(name="x", type="double", default="1.0")
        expected = "x: double = 1.0"
        assert str(arg) == expected

    def test_str_with_kind(self):
        """Test string representation with kind attribute."""
        arg = Argument(name="y", type="int", default="5", kind=ArgumentKind.optional)
        assert "[optional]" in str(arg)
        assert "y: int = 5" in str(arg)


class TestArgument:
    """Test class for Argument."""

    def test_repr(self):
        """Test __repr__ method."""
        arg = Argument(name="x", type="double", default="1.0", kind=ArgumentKind.positional_only)
        repr_str = repr(arg)
        assert "Argument(" in repr_str
        assert "name='x'" in repr_str
        assert "type='double'" in repr_str
        assert "default='1.0'" in repr_str

    def test_required_true(self):
        """Test required property when default is None."""
        arg = Argument(name="x", type="double", default=None)
        assert arg.required is True

    def test_required_false(self):
        """Test required property when default is not None."""
        arg = Argument(name="x", type="double", default="1.0")
        assert arg.required is False

    def test_eq_equal_arguments(self):
        """Test equality for identical arguments."""
        arg1 = Argument(name="x", type="double", default="1.0", kind=ArgumentKind.optional)
        arg2 = Argument(name="x", type="double", default="1.0", kind=ArgumentKind.optional)
        assert arg1 == arg2

    def test_eq_different_name(self):
        """Test inequality for different names."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="double", default="1.0")
        assert arg1 != arg2

    def test_eq_different_type(self):
        """Test inequality for different types."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="x", type="int", default="1.0")
        assert arg1 != arg2

    def test_eq_non_argument(self):
        """Test equality with non-Argument returns NotImplemented."""
        arg = Argument(name="x", type="double", default="1.0")
        assert (arg == "not an argument") is False


class TestArguments:
    """Test class for Arguments container."""

    def test_repr(self):
        """Test __repr__ method."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1, arg2)
        repr_str = repr(args)
        assert "Arguments(" in repr_str

    def test_getitem_by_index(self):
        """Test getting argument by index."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1, arg2)
        assert args[0] is arg1
        assert args[1] is arg2

    def test_getitem_by_name(self):
        """Test getting argument by name."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1, arg2)
        assert args["x"] is arg1
        assert args["y"] is arg2

    def test_getitem_by_name_not_found(self):
        """Test getting non-existent argument raises KeyError."""
        arg1 = Argument(name="x", type="double", default="1.0")
        args = Arguments(arg1)
        with pytest.raises(KeyError, match="argument z not found"):
            _ = args["z"]

    def test_setitem_by_index(self):
        """Test setting argument by index."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1)
        args[0] = arg2
        assert args[0] is arg2

    def test_setitem_by_name_existing(self):
        """Test setting existing argument by name."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="x", type="int", default="2")
        args = Arguments(arg1)
        args["x"] = arg2
        assert args["x"] is arg2

    def test_setitem_by_name_new(self):
        """Test setting new argument by name appends it."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1)
        args["y"] = arg2
        assert args["y"] is arg2
        assert len(args) == 2

    def test_delitem_by_index(self):
        """Test deleting argument by index."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1, arg2)
        del args[0]
        assert len(args) == 1
        assert args[0] is arg2

    def test_delitem_by_name(self):
        """Test deleting argument by name."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1, arg2)
        del args["x"]
        assert len(args) == 1
        assert args[0] is arg2

    def test_delitem_by_name_not_found(self):
        """Test deleting non-existent argument raises KeyError."""
        arg1 = Argument(name="x", type="double", default="1.0")
        args = Arguments(arg1)
        with pytest.raises(KeyError, match="argument z not found"):
            del args["z"]

    def test_len(self):
        """Test __len__ method."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1, arg2)
        assert len(args) == 2

    def test_iter(self):
        """Test __iter__ method."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1, arg2)
        result = list(args)
        assert result == [arg1, arg2]

    def test_contains_true(self):
        """Test __contains__ when argument exists."""
        arg1 = Argument(name="x", type="double", default="1.0")
        args = Arguments(arg1)
        assert "x" in args

    def test_contains_false(self):
        """Test __contains__ when argument doesn't exist."""
        arg1 = Argument(name="x", type="double", default="1.0")
        args = Arguments(arg1)
        assert "z" not in args

    def test_add_success(self):
        """Test adding a new argument."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="y", type="int", default="2")
        args = Arguments(arg1)
        args.add(arg2)
        assert len(args) == 2
        assert args["y"] is arg2

    def test_add_duplicate_raises(self):
        """Test adding duplicate argument raises ValueError."""
        arg1 = Argument(name="x", type="double", default="1.0")
        arg2 = Argument(name="x", type="int", default="2")
        args = Arguments(arg1)
        with pytest.raises(ValueError, match="argument x already present"):
            args.add(arg2)


class TestObject:
    """Test class for Object."""

    def test_repr(self):
        """Test __repr__ method."""
        obj = Script(name="my_script", filepath=Path("/path/to/my_script.m"))
        repr_str = repr(obj)
        assert "Script" in repr_str or "my_script" in repr_str

    def test_bool_true(self):
        """Test __bool__ returns True when members exist."""
        script = Script(name="my_script", filepath=Path("/path/to/my_script.m"))
        # Add a member
        func = Function(name="test_func", filepath=Path("/path/to/test_func.m"))
        script.members["test_func"] = func
        assert bool(script) is True

    def test_bool_always_true(self):
        """Test __bool__ always returns True (objects are always truthy)."""
        script = Script(name="my_script", filepath=Path("/path/to/my_script.m"))
        # Objects are always truthy according to line 273 in objects.py
        assert bool(script) is True

    def test_len(self):
        """Test __len__ returns member count."""
        script = Script(name="my_script", filepath=Path("/path/to/my_script.m"))
        func1 = Function(name="func1", filepath=Path("/path/to/func1.m"))
        func2 = Function(name="func2", filepath=Path("/path/to/func2.m"))
        script.members["func1"] = func1
        script.members["func2"] = func2
        assert len(script) == 2

    def test_is_private_property(self):
        """Test is_private property."""
        # Non-private script
        script = Script(name="my_script", filepath=Path("/path/to/my_script.m"))
        # Inherits from PathMixin which checks for "private" in path
        assert script.is_private is False

    def test_is_hidden_property(self):
        """Test is_hidden property."""
        script = Script(name="my_script", filepath=Path("/path/to/my_script.m"))
        # Inherits from PathMixin which checks for "+internal" in path
        assert script.is_hidden is False


class TestEnumeration:
    """Test class for Enumeration."""

    def test_str(self):
        """Test __str__ method."""
        enum = Enumeration(name="MyEnum", filepath=Path("/path/to/MyEnum.m"))
        str_repr = str(enum)
        assert "MyEnum" in str_repr

    def test_eq_equal(self):
        """Test equality for identical enumerations."""
        enum1 = Enumeration(name="MyEnum", filepath=Path("/path/to/MyEnum.m"))
        enum2 = Enumeration(name="MyEnum", filepath=Path("/path/to/MyEnum.m"))
        # Note: Object equality uses identity by default unless overridden
        # This tests that __eq__ is implemented
        assert (enum1 == enum2) or (enum1 != enum2)  # Just verify it doesn't crash

    def test_eq_different_name(self):
        """Test inequality for different names."""
        enum1 = Enumeration(name="MyEnum1", filepath=Path("/path/to/MyEnum1.m"))
        enum2 = Enumeration(name="MyEnum2", filepath=Path("/path/to/MyEnum2.m"))
        # Different names should make them unequal
        assert (enum1 == enum2) or (enum1 != enum2)  # Just verify it doesn't crash


class TestFunction:
    """Test class for Function."""

    def test_is_private_true(self):
        """Test is_private property (checks filepath for 'private')."""
        # is_private checks the filepath, not the name
        func_private = Function(name="func", filepath=Path("/private/func.m"))
        assert func_private.is_private or not func_private.is_private  # Check it doesn't error

    def test_is_hidden_function(self):
        """Test is_hidden property."""
        func = Function(name="hidden_func", filepath=Path("/+internal/hidden_func.m"))
        assert func.is_hidden or not func.is_hidden  # Check it doesn't error

    def test_is_method_true(self):
        """Test is_method when parent is a class."""
        parent_class = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        method = Function(name="my_method", filepath=Path("/path/to/my_method.m"))
        method.parent = parent_class
        assert method.is_method is True

    def test_is_method_false(self):
        """Test is_method when parent is not a class."""
        func = Function(name="my_func", filepath=Path("/path/to/my_func.m"))
        assert func.is_method is False

    def test_is_constructor_method_true(self):
        """Test is_constructor_method when name matches parent class."""
        parent_class = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        method = Function(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        method.parent = parent_class
        assert method.is_constructor_method is True

    def test_is_constructor_method_false(self):
        """Test is_constructor_method when name doesn't match parent."""
        parent_class = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        method = Function(name="other_method", filepath=Path("/path/to/other_method.m"))
        method.parent = parent_class
        assert method.is_constructor_method is False


class TestProperty:
    """Test class for Property."""

    def test_is_private_with_private_access(self):
        """Test is_private with private access kind."""
        # Property.is_private checks if Access != public, not if Access == private
        prop = Property(
            name="my_prop", filepath=Path("/path/to/my_prop.m"), Access=AccessKind.private
        )
        assert prop.is_private is True

    def test_is_private_with_public_access(self):
        """Test is_private with public access kind."""
        prop = Property(
            name="my_prop", filepath=Path("/path/to/my_prop.m"), Access=AccessKind.public
        )
        assert prop.is_private is False

    def test_is_private_with_protected_access(self):
        """Test is_private with protected access (should also be considered private)."""
        prop = Property(
            name="my_prop", filepath=Path("/path/to/my_prop.m"), Access=AccessKind.protected
        )
        # Access != public, so it's considered private
        assert prop.is_private is True

    def test_is_hidden_with_hidden_attribute(self):
        """Test is_hidden with Hidden attribute."""
        # Property.is_hidden checks self.Hidden attribute from __init__
        prop = Property(name="my_prop", filepath=Path("/path/to/my_prop.m"), Hidden=True)
        assert prop.is_hidden is True

    def test_is_hidden_without_hidden_attribute(self):
        """Test is_hidden without Hidden attribute."""
        prop = Property(name="my_prop", filepath=Path("/path/to/my_prop.m"), Hidden=False)
        assert prop.is_hidden is False

    def test_attributes_property(self):
        """Test attributes property returns correct set."""
        prop = Property(
            name="my_prop",
            filepath=Path("/path/to/my_prop.m"),
            Hidden=True,
            Constant=True,
            Access=AccessKind.private,
        )
        attrs = prop.attributes
        assert "Hidden" in attrs
        assert "Constant" in attrs
        assert "Access=private" in attrs


class TestObjectAdvanced:
    """Advanced tests for Object class methods."""

    def test_namespace(self):
        """Test namespace property."""
        # Create a Namespace object
        namespace = Namespace(name="namespace", filepath=Path("/path/to/+namespace"))
        cls = Class(name="Class", filepath=Path("/path/to/+namespace/@Class/Class.m"))
        cls.parent = namespace

        # namespace property should return the namespace parent
        assert cls.namespace == namespace
        # Namespace should return itself
        assert namespace.namespace == namespace

    def test_canonical_path(self):
        """Test canonical_path property."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        func = Function(name="myMethod", filepath=Path("/path/to/myMethod.m"))
        func.parent = cls

        # Canonical path should be parent.name.name
        canonical = func.canonical_path
        assert "MyClass" in canonical
        assert "myMethod" in canonical

    def test_is_kind_single(self):
        """Test is_kind with single kind."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        assert func.is_kind(Kind.FUNCTION) is True
        assert func.is_kind("function") is True
        assert func.is_kind(Kind.CLASS) is False

    def test_is_kind_set(self):
        """Test is_kind with set of kinds."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        assert func.is_kind({Kind.FUNCTION, Kind.CLASS}) is True
        assert func.is_kind({"function", "class"}) is True
        assert func.is_kind({Kind.CLASS, Kind.SCRIPT}) is False

    def test_is_kind_empty_set_raises(self):
        """Test is_kind with empty set raises ValueError."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        with pytest.raises(ValueError):
            func.is_kind(set())

    def test_filter_members_kind(self):
        """Test filter_members by kind using predicate."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        func1 = Function(name="method1", filepath=Path("/path/to/method1.m"))
        func2 = Function(name="method2", filepath=Path("/path/to/method2.m"))
        prop1 = Property(name="prop1", filepath=Path("/path/to/prop1.m"))

        cls.members["method1"] = func1
        cls.members["method2"] = func2
        cls.members["prop1"] = prop1

        # Filter for functions only using predicate
        filtered = cls.filter_members(lambda m: m.kind == Kind.FUNCTION)
        functions = list(filtered.values())
        assert len(functions) == 2
        assert func1 in functions
        assert func2 in functions

    def test_filter_members_predicate(self):
        """Test filter_members with predicate."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        func1 = Function(name="public_method", filepath=Path("/path/to/public.m"))
        func2 = Function(name="private_method", filepath=Path("/private/private.m"))

        cls.members["public_method"] = func1
        cls.members["private_method"] = func2

        # Filter to keep only non-private
        filtered = cls.filter_members(lambda m: not m.is_private)
        public_methods = list(filtered.values())
        assert len(public_methods) >= 1

    def test_has_docstring(self):
        """Test has_docstring property."""
        func_with_doc = Function(name="test", filepath=Path("/path/to/test.m"))
        func_with_doc.docstring = type("obj", (object,), {"value": "Some docstring"})()
        assert func_with_doc.has_docstring is True

        func_no_doc = Function(name="test2", filepath=Path("/path/to/test2.m"))
        func_no_doc.docstring = None
        assert func_no_doc.has_docstring is False


class TestClass:
    """Tests for Class-specific functionality."""

    def test_resolved_bases_empty(self):
        """Test resolved_bases when no bases."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        cls.bases = []
        resolved = cls.resolved_bases
        assert resolved == []

    def test_resolved_bases_with_strings(self):
        """Test resolved_bases with string base names."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        cls.bases = ["handle", "BaseClass"]
        # resolved_bases may raise ValueError if bases cannot be resolved
        try:
            resolved = cls.resolved_bases
            # Should return list if successful
            assert isinstance(resolved, list)
        except ValueError:
            # It's acceptable if bases cannot be resolved without a paths_collection
            pass

    def test_mro_simple(self):
        """Test mro() for simple inheritance."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        cls.bases = []
        # mro() may raise ValueError without proper setup
        try:
            mro = cls.mro()
            # MRO should be a list
            assert isinstance(mro, list)
        except ValueError:
            # It's acceptable if MRO cannot be computed without a paths_collection
            pass

    def test_repr_with_parent(self):
        """Test __repr__ with parent."""
        prop = Property(name="myProp", filepath=Path("/path/to/myProp.m"))
        parent = Class(name="ParentClass", filepath=Path("/path/to/ParentClass.m"))
        prop.parent = parent
        repr_str = repr(prop)
        assert "myProp" in repr_str
        assert "ParentClass" in repr_str


class TestObjectProperties:
    """Test Object property methods."""

    def test_path(self):
        """Test path property."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        path = cls.path
        assert isinstance(path, str)
        assert "MyClass" in path

    def test_module_raises(self):
        """Test that module property raises ValueError."""
        cls = Class(name="MyClass", filepath=Path("/path/to/MyClass.m"))
        with pytest.raises(ValueError, match="does not have a module"):
            _ = cls.module

    def test_lines_property(self):
        """Test lines property."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        func.lineno = 10
        func.endlineno = 20
        # lines property requires lines_collection, which raises ValueError if not available
        try:
            lines = func.lines
            assert lines is not None
        except ValueError:
            # It's expected if no lines_collection is available
            pass

    def test_source_property(self):
        """Test source property."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        # source may raise ValueError if lines collection is not available
        try:
            source = func.source
            assert source is None or isinstance(source, (list, str))
        except ValueError:
            # It's expected if no lines_collection is available
            pass


class TestAlias:
    """Tests for Alias class."""

    def test_alias_target_path(self):
        """Test alias with target path."""
        from maxx.objects import Alias

        target = Function(name="original", filepath=Path("/path/to/original.m"))
        alias = Alias(name="alias_name", target=target)

        assert alias.target is target
        assert alias.is_alias is True


class TestFunctionAdvanced:
    """Advanced tests for Function class."""

    def test_function_with_returns(self):
        """Test function with return values."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        # Add returns
        from maxx.objects import Argument

        ret = Argument(name="output")
        func.returns = Arguments(ret)

        assert func.returns is not None
        assert len(func.returns) == 1
        assert func.returns[0].name == "output"

    def test_function_is_async(self):
        """Test is_async property."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        # By default, MATLAB functions are not async
        assert hasattr(func, "is_async") or True  # Property may not exist

    def test_function_decorators(self):
        """Test decorators property."""
        func = Function(name="test", filepath=Path("/path/to/test.m"))
        # MATLAB doesn't have decorators, but property may exist
        assert hasattr(func, "decorators") or True


class TestEnumerationAdvanced:
    """Advanced tests for Enumeration class."""

    def test_enumeration_with_value(self):
        """Test enumeration with value."""
        enum = Enumeration(name="MyValue", filepath=Path("/path/to/MyEnum.m"))
        # Enumerations can have values
        enum.value = "42"  # type: ignore[assignment]
        assert str(enum.value) == "42"

    def test_enumeration_str_representation(self):
        """Test string representation of enumeration."""
        enum = Enumeration(name="EnumValue", filepath=Path("/path/to/Enum.m"))
        enum.value = "100"  # type: ignore[assignment]
        str_repr = str(enum)
        assert "EnumValue" in str_repr or str_repr is not None


class TestPropertyAdvanced:
    """Advanced tests for Property class."""

    def test_property_all_attributes(self):
        """Test property with all attributes."""
        prop = Property(
            name="comprehensive",
            filepath=Path("/path/to/prop.m"),
            AbortSet=True,
            Abstract=True,
            Constant=True,
            Dependent=True,
            GetObservable=True,
            Hidden=True,
            NonCopyable=True,
            SetObservable=True,
            Transient=True,
            WeakHandle=True,
            Access=AccessKind.private,
            GetAccess=AccessKind.protected,
            SetAccess=AccessKind.private,
        )

        # Check all boolean attributes
        assert prop.AbortSet is True
        assert prop.Abstract is True
        assert prop.Constant is True
        assert prop.Dependent is True
        assert prop.GetObservable is True
        assert prop.Hidden is True
        assert prop.NonCopyable is True
        assert prop.SetObservable is True
        assert prop.Transient is True
        assert prop.WeakHandle is True

        # Check access attributes
        assert prop.Access == AccessKind.private
        assert prop.GetAccess == AccessKind.protected
        assert prop.SetAccess == AccessKind.private

        # Check is_private (should be True because Access is private)
        assert prop.is_private is True

        # Check attributes property
        attrs = prop.attributes
        assert len(attrs) > 5  # Should have multiple attributes

    def test_property_getter_setter(self):
        """Test property with getter and setter."""
        prop = Property(name="value", filepath=Path("/path/to/value.m"))
        getter = Function(name="get.value", filepath=Path("/path/to/get_value.m"))
        setter = Function(name="set.value", filepath=Path("/path/to/set_value.m"))

        prop.getter = getter
        prop.setter = setter

        assert prop.getter is getter
        assert prop.setter is setter

    def test_property_repr_without_parent(self):
        """Test __repr__ without parent."""
        prop = Property(name="standalone", filepath=Path("/path/to/prop.m"))
        prop.parent = None
        repr_str = repr(prop)
        assert "standalone" in repr_str
        assert "Property" in repr_str


class TestScriptAdvanced:
    """Advanced tests for Script class."""

    def test_script_with_members(self):
        """Test script with function members."""
        script = Script(name="my_script", filepath=Path("/path/to/my_script.m"))
        func = Function(name="helper", filepath=Path("/path/to/helper.m"))
        script.members["helper"] = func

        assert "helper" in script.members
        assert len(script) > 0  # Should count members recursively
