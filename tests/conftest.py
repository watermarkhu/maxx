"""Configuration for pytest."""

from pathlib import Path

import pytest


@pytest.fixture
def test_files_dir():
    """Return the path to the test files directory."""
    return Path(__file__).parent / "files"
