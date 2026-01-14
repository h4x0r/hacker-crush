#!/bin/bash
# Build script for Pygbag (Python to WebAssembly)

set -e

echo "=== Hacker Crush Build ==="

# Ensure pygbag is installed
if ! command -v pygbag &> /dev/null; then
    echo "Installing pygbag..."
    pip install pygbag
fi

# Clean previous build
rm -rf build/web

# Create build directory
mkdir -p build/web

# Run pygbag to compile to WebAssembly
echo "Compiling to WebAssembly..."
pygbag --build src

# Move output to build/web
mv src/build/web/* build/web/
rm -rf src/build

echo "=== Build Complete ==="
echo "Output: build/web/"
echo ""
echo "To test locally: python -m http.server -d build/web 8000"
echo "Then open: http://localhost:8000"
