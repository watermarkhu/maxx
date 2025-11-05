"""Tests for the exceptions module."""

import pytest

from maxx.exceptions import CyclicAliasError, FilePathError, MaltError, NameResolutionError


class TestMaltError:
    """Test class for MaltError."""

    def test_malt_error_base(self):
        """Test that MaltError can be raised and caught."""
        with pytest.raises(MaltError):
            raise MaltError("Test error")


class TestCyclicAliasError:
    """Test class for CyclicAliasError."""

    def test_cyclic_alias_error_initialization(self):
        """Test that CyclicAliasError initializes correctly with a chain."""
        chain = ["A", "B", "C", "A"]
        error = CyclicAliasError(chain)

        assert error.chain == chain
        assert "Cyclic aliases detected:" in str(error)
        assert "A" in str(error)
        assert "B" in str(error)
        assert "C" in str(error)

    def test_cyclic_alias_error_raise(self):
        """Test that CyclicAliasError can be raised and caught."""
        chain = ["X", "Y", "Z", "X"]
        with pytest.raises(CyclicAliasError) as exc_info:
            raise CyclicAliasError(chain)

        assert exc_info.value.chain == chain

    def test_cyclic_alias_error_message_format(self):
        """Test that the error message is formatted correctly."""
        chain = ["First", "Second", "Third"]
        error = CyclicAliasError(chain)
        error_message = str(error)

        assert error_message.startswith("Cyclic aliases detected:")
        for item in chain:
            assert item in error_message


class TestFilePathError:
    """Test class for FilePathError."""

    def test_filepath_error(self):
        """Test that FilePathError can be raised and caught."""
        with pytest.raises(FilePathError):
            raise FilePathError("Cannot access filepath")

    def test_filepath_error_is_malt_error(self):
        """Test that FilePathError is a subclass of MaltError."""
        assert issubclass(FilePathError, MaltError)


class TestNameResolutionError:
    """Test class for NameResolutionError."""

    def test_name_resolution_error(self):
        """Test that NameResolutionError can be raised and caught."""
        with pytest.raises(NameResolutionError):
            raise NameResolutionError("Cannot resolve name")

    def test_name_resolution_error_is_malt_error(self):
        """Test that NameResolutionError is a subclass of MaltError."""
        assert issubclass(NameResolutionError, MaltError)
