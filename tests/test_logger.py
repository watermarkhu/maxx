"""Tests for the logger module."""

import logging
import sys

from maxx.logger import InterceptHandler, configure


class TestInterceptHandler:
    """Test class for InterceptHandler."""

    def test_emit_standard_level(self):
        """Test that InterceptHandler can emit a log record with standard level."""
        handler = InterceptHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Should not raise an exception
        handler.emit(record)

    def test_emit_custom_level(self):
        """Test that InterceptHandler can handle custom log levels."""
        handler = InterceptHandler()
        record = logging.LogRecord(
            name="test",
            level=99,  # Custom level
            pathname="test.py",
            lineno=1,
            msg="Custom level message",
            args=(),
            exc_info=None,
        )
        # Should not raise an exception
        handler.emit(record)

    def test_emit_with_exception(self):
        """Test that InterceptHandler can emit a log record with exception info."""
        handler = InterceptHandler()
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error message",
                args=(),
                exc_info=exc_info,
            )
            # Should not raise an exception
            handler.emit(record)


class TestConfigure:
    """Test class for the configure function."""

    def test_configure_default_level(self):
        """Test configure with default INFO level."""
        configure()
        # Should complete without error

    def test_configure_debug_level(self):
        """Test configure with DEBUG level."""
        configure(level="DEBUG")
        # Should complete without error

    def test_configure_warning_level(self):
        """Test configure with WARNING level."""
        configure(level="WARNING")
        # Should complete without error

    def test_configure_error_level(self):
        """Test configure with ERROR level."""
        configure(level="ERROR")
        # Should complete without error

    def test_configure_critical_level(self):
        """Test configure with CRITICAL level."""
        configure(level="CRITICAL")
        # Should complete without error

    def test_configure_with_format(self):
        """Test configure with custom format."""
        configure(level="INFO", format="{time} - {message}")
        # Should complete without error

    def test_intercept_standard_logging(self):
        """Test that standard logging is intercepted by loguru."""
        # Just verify that configure doesn't raise an error
        # and that logging integration works
        configure(level="INFO")

        # Create a standard logger
        std_logger = logging.getLogger("test_standard")
        # This should not raise an error
        std_logger.info("Test standard logging")
