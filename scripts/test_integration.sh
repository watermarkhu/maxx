#!/bin/bash
# Integration test script for maxx/malt
# Builds the Rust library and runs comparison tests

set -e  # Exit on error

echo "========================================="
echo "maxx/malt Integration Test Suite"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "Cargo.toml" ]; then
    echo -e "${RED}Error: Must run from project root${NC}"
    exit 1
fi

# Step 1: Run Rust tests
echo -e "${YELLOW}Step 1/4: Running Rust unit tests...${NC}"
cargo test || {
    echo -e "${RED}Rust tests failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓ Rust tests passed${NC}"
echo ""

# Step 2: Build Rust with Python bindings
echo -e "${YELLOW}Step 2/4: Building Rust library with Python bindings...${NC}"
if ! command -v maturin &> /dev/null; then
    echo "maturin not found, installing..."
    pip install maturin
fi

maturin develop --features python || {
    echo -e "${RED}Failed to build Python bindings!${NC}"
    exit 1
}
echo -e "${GREEN}✓ Python bindings built${NC}"
echo ""

# Step 3: Verify malt can be imported
echo -e "${YELLOW}Step 3/4: Verifying malt installation...${NC}"
python -c "import malt; print(f'malt version: {malt.__version__}')" || {
    echo -e "${RED}Failed to import malt!${NC}"
    exit 1
}
echo -e "${GREEN}✓ malt successfully imported${NC}"
echo ""

# Step 4: Run integration tests
echo -e "${YELLOW}Step 4/4: Running integration tests (maxx vs malt)...${NC}"
pytest tests/test_integration_maxx_malt.py -v || {
    echo -e "${RED}Integration tests failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓ Integration tests passed${NC}"
echo ""

echo "========================================="
echo -e "${GREEN}All tests passed! ✅${NC}"
echo "Python (maxx) and Rust (malt) implementations are compatible!"
echo "========================================="
