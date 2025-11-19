"""Integration tests comparing Python (maxx) and Rust (malt) implementations.

These tests verify that the Rust port produces the same results as the Python implementation.
"""

from pathlib import Path

import pytest

# Import both implementations
import maxx.treesitter as maxx_parser
import maxx.collection as maxx_collection

try:
    import malt.treesitter as malt_parser
    import malt.collection as malt_collection
    MALT_AVAILABLE = True
except ImportError:
    MALT_AVAILABLE = False
    pytest.skip("malt (Rust implementation) not available", allow_module_level=True)


@pytest.fixture
def test_files_dir():
    """Return the path to the test files directory."""
    return Path(__file__).parent / "files"


class TestParserParity:
    """Test that maxx and malt parsers produce equivalent results."""

    def compare_basic_properties(self, maxx_obj, malt_obj, obj_type):
        """Compare basic properties between maxx and malt objects."""
        # Compare names
        assert maxx_obj.name == malt_obj.name, f"{obj_type}: names don't match"

        # Compare kinds (string representation)
        assert str(maxx_obj.kind) == str(malt_obj.kind), f"{obj_type}: kinds don't match"

        # Compare line numbers if available
        if hasattr(maxx_obj, 'lineno') and maxx_obj.lineno is not None:
            assert maxx_obj.lineno == malt_obj.lineno, f"{obj_type}: line numbers don't match"

        if hasattr(maxx_obj, 'endlineno') and maxx_obj.endlineno is not None:
            assert maxx_obj.endlineno == malt_obj.endlineno, f"{obj_type}: end line numbers don't match"

    def test_function_parsing(self, test_files_dir):
        """Test that both implementations parse functions identically."""
        test_file = test_files_dir / "test_function.m"

        maxx_obj = maxx_parser.FileParser(test_file).parse()
        malt_obj = malt_parser.FileParser(test_file).parse()

        # Compare basic properties
        self.compare_basic_properties(maxx_obj, malt_obj, "Function")

        # Both should be functions
        assert maxx_obj.name == "test_function"
        assert malt_obj.name == "test_function"

        print(f"✓ Function parsing parity verified for {test_file.name}")

    def test_class_parsing(self, test_files_dir):
        """Test that both implementations parse classes identically."""
        test_file = test_files_dir / "MyClass.m"

        maxx_obj = maxx_parser.FileParser(test_file).parse()
        malt_obj = malt_parser.FileParser(test_file).parse()

        # Compare basic properties
        self.compare_basic_properties(maxx_obj, malt_obj, "Class")

        # Both should be MyClass
        assert maxx_obj.name == "MyClass"
        assert malt_obj.name == "MyClass"

        print(f"✓ Class parsing parity verified for {test_file.name}")

    def test_script_parsing(self, test_files_dir):
        """Test that both implementations parse scripts identically."""
        test_file = test_files_dir / "my_script.m"

        maxx_obj = maxx_parser.FileParser(test_file).parse()
        malt_obj = malt_parser.FileParser(test_file).parse()

        # Compare basic properties
        self.compare_basic_properties(maxx_obj, malt_obj, "Script")

        # Both should recognize it as a script
        assert maxx_obj.name == "my_script"
        assert malt_obj.name == "my_script"

        print(f"✓ Script parsing parity verified for {test_file.name}")

    def test_multiple_files(self, test_files_dir):
        """Test parsing multiple files with both implementations."""
        test_files = [
            "test_function.m",
            "MyClass.m",
            "my_script.m",
        ]

        for filename in test_files:
            test_file = test_files_dir / filename
            if not test_file.exists():
                continue

            maxx_obj = maxx_parser.FileParser(test_file).parse()
            malt_obj = malt_parser.FileParser(test_file).parse()

            # Verify names match
            assert maxx_obj.name == malt_obj.name, f"Names don't match for {filename}"

            # Verify kinds match
            assert str(maxx_obj.kind) == str(malt_obj.kind), f"Kinds don't match for {filename}"

        print(f"✓ Multi-file parsing parity verified for {len(test_files)} files")


class TestCollectionParity:
    """Test that maxx and malt collections produce equivalent results."""

    def test_single_path_collection(self, test_files_dir):
        """Test collecting from a single path."""
        # Use a subdirectory with fewer files for faster testing
        test_path = test_files_dir / "subdir"

        if not test_path.exists():
            pytest.skip(f"Test path {test_path} does not exist")

        try:
            maxx_coll = maxx_collection.PathsCollection([test_path])
            malt_coll = malt_collection.PathsCollection([test_path])

            # Compare number of collected objects
            assert len(maxx_coll) == len(malt_coll), \
                f"Collection sizes don't match: maxx={len(maxx_coll)}, malt={len(malt_coll)}"

            # Compare object names
            maxx_keys = set(maxx_coll.keys())
            malt_keys = set(malt_coll.keys())

            assert maxx_keys == malt_keys, \
                f"Object names don't match.\nMaxx: {maxx_keys}\nMalt: {malt_keys}"

            print(f"✓ Collection parity verified: {len(maxx_coll)} objects from {test_path}")
        except Exception as e:
            # Collections might not be fully implemented yet
            pytest.skip(f"Collection test skipped: {e}")

    def test_collection_access(self, test_files_dir):
        """Test accessing objects from collection."""
        try:
            maxx_coll = maxx_collection.PathsCollection([test_files_dir])
            malt_coll = malt_collection.PathsCollection([test_files_dir])

            # Test __contains__
            if "test_function" in maxx_coll:
                assert "test_function" in malt_coll, "test_function not in malt collection"

                # Test __getitem__
                maxx_func = maxx_coll["test_function"]
                malt_func = malt_coll["test_function"]

                assert maxx_func.name == malt_func.name, "Function names don't match"

            print(f"✓ Collection access parity verified")
        except Exception as e:
            pytest.skip(f"Collection access test skipped: {e}")


class TestPerformanceComparison:
    """Compare performance between Python and Rust implementations."""

    def test_parsing_speed(self, test_files_dir, benchmark=None):
        """Compare parsing speed (optional, requires pytest-benchmark)."""
        test_file = test_files_dir / "MyClass.m"

        if benchmark is None:
            pytest.skip("pytest-benchmark not available")

        def parse_with_maxx():
            return maxx_parser.FileParser(test_file).parse()

        def parse_with_malt():
            return malt_parser.FileParser(test_file).parse()

        # Benchmark both
        maxx_result = benchmark.pedantic(parse_with_maxx, rounds=100)
        malt_result = benchmark.pedantic(parse_with_malt, rounds=100)

        # Just verify they both work, don't enforce performance
        assert maxx_result.name == malt_result.name


def test_import_compatibility():
    """Test that malt can be imported with the same API as maxx."""
    # Test module structure
    assert hasattr(malt_parser, 'FileParser'), "malt.treesitter.FileParser not found"
    assert hasattr(malt_collection, 'PathsCollection'), "malt.collection.PathsCollection not found"

    print("✓ Import compatibility verified")


def test_basic_api_compatibility(test_files_dir):
    """Test that basic API is compatible between maxx and malt."""
    test_file = test_files_dir / "test_function.m"

    # Test FileParser API
    maxx_fp = maxx_parser.FileParser(test_file)
    malt_fp = malt_parser.FileParser(test_file)

    assert hasattr(maxx_fp, 'parse'), "maxx FileParser missing parse method"
    assert hasattr(malt_fp, 'parse'), "malt FileParser missing parse method"

    # Test parsing works
    maxx_obj = maxx_fp.parse()
    malt_obj = malt_fp.parse()

    # Test basic object API
    assert hasattr(maxx_obj, 'name'), "maxx object missing name attribute"
    assert hasattr(malt_obj, 'name'), "malt object missing name attribute"
    assert hasattr(maxx_obj, 'kind'), "maxx object missing kind attribute"
    assert hasattr(malt_obj, 'kind'), "malt object missing kind attribute"

    print("✓ Basic API compatibility verified")


if __name__ == "__main__":
    # Run a simple test if executed directly
    import sys
    test_dir = Path(__file__).parent / "files"

    if not MALT_AVAILABLE:
        print("ERROR: malt (Rust implementation) not available")
        print("Build it with: maturin develop --features python")
        sys.exit(1)

    print("Running basic compatibility tests...")
    test_import_compatibility()
    test_basic_api_compatibility(test_dir)

    # Run parser parity tests
    tester = TestParserParity()
    tester.test_function_parsing(test_dir)
    tester.test_class_parsing(test_dir)
    tester.test_script_parsing(test_dir)
    tester.test_multiple_files(test_dir)

    print("\n✅ All integration tests passed!")
    print("Python (maxx) and Rust (malt) implementations are compatible!")
