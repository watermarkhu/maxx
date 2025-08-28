from pathlib import Path

import pytest

from maxx.collection import PathsCollection

try:
    import matlab.engine
except ImportError:
    pytest.skip("matlab.engine not available", allow_module_level=True)


TEST_FILES_DIR = Path(__file__).parent / "files"


class TestMatlabPath:
    """Test class for the PathsCollection class."""

    @pytest.fixture(autouse=True)
    def setup(self, test_files_dir):
        """Set up the test by initializing a PathsCollection with test files."""
        paths = [test_files_dir]
        self.paths_collection = PathsCollection(
            paths, recursive=True, working_directory=TEST_FILES_DIR
        )
        self.engine = matlab.engine.start_matlab()
        for path in paths:
            self.engine.addpath(str(path))

    @pytest.mark.parametrize(
        "call",
        [
            "TestClass",
            "test_function",
            "plot_axes",
            "test_script",
            "ClassFolder",
            "namespace.NamespaceClass",
            "namespace.test_namespace_function",
        ],
    )
    def test_with_call(self, call):
        """Test method that uses the 'call' parameter."""
        # Replace the following with actual test logic using 'call'
        try:
            path_matlab = Path(self.engine.which(call)).resolve()
        except Exception as e:
            pytest.fail(f"Error occurred while resolving {call} in MATLAB: {e}")

        try:
            path_python = self.paths_collection._mapping[call][0]
        except Exception as e:
            pytest.fail(f"Error occurred while resolving {call} in Python: {e}")

        assert path_matlab == path_python, f"Paths do not match for {call}"
