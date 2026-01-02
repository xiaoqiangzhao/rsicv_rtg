#!/bin/bash
# Skill: Generate C++ headers and source from YAML definitions
# Usage: skill-generate-cpp [options]
# Options:
#   --clean        Clean generated files before generation
#   --copy         Copy generated headers to shader system include directory
#   --test         Run integration test after generation
#   --help         Show this help

CLEAN=false
COPY=false
TEST=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --copy)
            COPY=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        --help)
            echo "Usage: skill-generate-cpp [options]"
            echo "Options:"
            echo "  --clean        Clean generated files before generation"
            echo "  --copy         Copy generated headers to shader system include directory"
            echo "  --test         Run integration test after generation"
            echo "  --help         Show this help"
            echo ""
            echo "Generates C++ headers and source files from unified RISC-V ISA YAML definitions:"
            echo "  - riscv_isa_generated.h: Instruction metadata and lookup tables"
            echo "  - riscv_isa_generated.cpp: Static data definitions"
            echo "  - test_shader_integration.py: Python integration test"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Generating C++ files from YAML definitions..."

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo "Cleaning generated files..."
    rm -f generated/riscv_isa_generated.h
    rm -f generated/riscv_isa_generated.cpp
    rm -f generated/test_shader_integration.py
fi

# Run generation script
python3 scripts/generate_cpp.py
if [ $? -ne 0 ]; then
    echo "❌ C++ generation failed!"
    exit 1
fi

echo "✅ C++ files generated:"
echo "  - generated/riscv_isa_generated.h"
echo "  - generated/riscv_isa_generated.cpp"
echo "  - generated/test_shader_integration.py"

# Copy to shader system if requested
if [ "$COPY" = true ]; then
    echo "Copying generated headers to shader system include directory..."
    cp generated/riscv_isa_generated.h ../shader_system/include/
    if [ $? -eq 0 ]; then
        echo "✅ Copied riscv_isa_generated.h to shader system"
    else
        echo "❌ Failed to copy to shader system!"
        exit 1
    fi
fi

# Run integration test if requested
if [ "$TEST" = true ]; then
    echo "Running shader system integration test..."
    python3 generated/test_shader_integration.py
    if [ $? -ne 0 ]; then
        echo "❌ Integration test failed!"
        exit 1
    fi
    echo "✅ Integration test passed!"
fi

echo "✅ C++ generation completed successfully!"