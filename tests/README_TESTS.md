# Testing Guide for maxx/malt

This directory contains tests for both the Python (maxx) and Rust (malt) implementations.

## Test Structure

- `test_*.py` - Python tests for the maxx library (original implementation)
- `test_integration_maxx_malt.py` - Integration tests comparing maxx and malt
- `rust_tests.rs` - Rust unit tests for the malt core library

## Running Tests

### Python Tests (maxx only)

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all Python tests
pytest tests/

# Run specific test file
pytest tests/test_treesitter.py

# Run with coverage
pytest --cov=maxx tests/
```

### Rust Tests (malt core)

```bash
# Run Rust unit tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_parse_function
```

### Integration Tests (maxx vs malt)

To run integration tests that compare Python and Rust implementations:

```bash
# 1. Build the Rust library with Python bindings
maturin develop --features python

# Or using pip
pip install maturin
maturin develop --features python

# 2. Run integration tests
pytest tests/test_integration_maxx_malt.py -v

# 3. Run standalone
python tests/test_integration_maxx_malt.py
```

## Building malt for Python

### Using maturin (recommended)

```bash
# Install maturin
pip install maturin

# Development build (debug, faster compilation)
maturin develop --features python

# Release build (optimized)
maturin develop --release --features python

# Build wheel
maturin build --release --features python
```

### Using pip (alternative)

```bash
# Install from source with Python bindings
pip install -e . --config-settings=build-args="--features python"
```

## Test Files

Test MATLAB files are located in `tests/files/`:

- `test_function.m` - Simple function with arguments
- `MyClass.m` - Class with properties, methods, inheritance
- `MyEnum.m` - Enumeration class
- `my_script.m` - Simple script file
- `@ClassFolder/` - Class folder structure
- `+namespace/` - Namespace package
- `subdir/` - Subdirectory with functions

## What the Integration Tests Verify

The integration tests (`test_integration_maxx_malt.py`) verify:

1. **Parser Parity**: Both implementations parse the same files identically
   - Function parsing
   - Class parsing
   - Script parsing
   - Multiple files

2. **Collection Parity**: Both implementations collect objects the same way
   - Single path collection
   - Object access patterns
   - Contains/getitem operations

3. **API Compatibility**: The Rust implementation provides the same Python API
   - Same module structure
   - Same class/method names
   - Same behavior

4. **Basic Properties**: Core attributes match
   - Object names
   - Object kinds
   - Line numbers

## Expected Results

When all tests pass, you should see:

```
✓ Function parsing parity verified
✓ Class parsing parity verified
✓ Script parsing parity verified
✓ Multi-file parsing parity verified
✓ Collection parity verified
✓ Collection access parity verified
✓ Import compatibility verified
✓ Basic API compatibility verified

✅ All integration tests passed!
```

## Troubleshooting

### malt not available

If you see "malt (Rust implementation) not available":

```bash
# Build the Python bindings
maturin develop --features python

# Verify it's installed
python -c "import malt; print('malt version:', malt.__version__)"
```

### Compilation errors

If you encounter compilation errors:

```bash
# Update Rust toolchain
rustup update

# Clean and rebuild
cargo clean
maturin develop --features python
```

### Test failures

If tests fail:

1. Check that test files exist in `tests/files/`
2. Verify both maxx and malt are properly installed
3. Run with verbose output: `pytest -vv`
4. Check individual implementation tests first:
   ```bash
   # Test maxx
   pytest tests/test_treesitter.py

   # Test malt core
   cargo test
   ```

## Performance Comparison

To compare performance (requires pytest-benchmark):

```bash
pip install pytest-benchmark
pytest tests/test_integration_maxx_malt.py::TestPerformanceComparison -v
```

## Continuous Integration

For CI/CD pipelines:

```bash
#!/bin/bash
set -e

# Install dependencies
pip install -e ".[dev]"
pip install maturin

# Build Rust with Python bindings
maturin develop --features python

# Run all tests
cargo test                              # Rust tests
pytest tests/ --ignore=tests/test_integration_maxx_malt.py  # Python tests
pytest tests/test_integration_maxx_malt.py -v  # Integration tests
```

## Contributing

When adding new features:

1. Add Python tests to `test_*.py`
2. Add Rust tests to `rust_tests.rs`
3. Add integration tests to `test_integration_maxx_malt.py`
4. Ensure all three test suites pass

This ensures feature parity between implementations.
