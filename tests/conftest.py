"""Configuration for pytest."""

import pytest
from pathlib import Path


@pytest.fixture
def test_files_dir():
    """Return the path to the test files directory."""
    return Path(__file__).parent / "files"
