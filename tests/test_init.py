"""Tests for the __init__ module."""

import logging

from maxx import ReturnTypeWarningFilter


class TestReturnTypeWarningFilter:
    """Test class for ReturnTypeWarningFilter."""

    def test_filter_with_return_type_warning(self):
        """Test that return type warnings are filtered out."""
        filter_obj = ReturnTypeWarningFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="No type or annotation for returned value in function foo",
            args=(),
            exc_info=None,
        )
        # Should return False to filter out the message
        assert filter_obj.filter(record) is False

    def test_filter_with_other_warning(self):
        """Test that other warnings are not filtered."""
        filter_obj = ReturnTypeWarningFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Some other warning message",
            args=(),
            exc_info=None,
        )
        # Should return True to allow the message
        assert filter_obj.filter(record) is True

    def test_filter_without_msg_attribute(self):
        """Test that records without msg attribute are not filtered."""
        filter_obj = ReturnTypeWarningFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg=None,
            args=(),
            exc_info=None,
        )
        # Should return True to allow the message
        assert filter_obj.filter(record) is True
