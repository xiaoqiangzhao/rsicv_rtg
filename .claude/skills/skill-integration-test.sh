#!/bin/bash
# Skill: Test shader system integration
# Usage: skill-integration-test [options]
# Options:
#   --generate     Generate C++ files first (if not already generated)
#   --copy         Copy generated headers to shader system before testing
#   --build        Build shader system tests after copying
#   --help         Show this help

GENERATE=false
COPY=false
BUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --generate)
            GENERATE=true
            shift
            ;;
        --copy)
            COPY=true
            shift
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --help)
            echo "Usage: skill-integration-test [options]"
            echo "Options:"
            echo "  --generate     Generate C++ files first (if not already generated)"
            echo "  --copy         Copy generated headers to shader system before testing"
            echo "  --build        Build shader system tests after copying"
            echo "  --help         Show this help"
            echo ""
            echo "Tests shader system integration by:"
            echo "  1. Running Python integration test (test_shader_integration.py)"
            echo "  2. Optionally generating C++ files from YAML definitions"
            echo "  3. Optionally copying headers to shader system include directory"
            echo "  4. Optionally building shader system tests"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Testing shader system integration..."

# Generate C++ files if requested
if [ "$GENERATE" = true ]; then
    echo "Generating C++ files from YAML definitions..."
    python3 scripts/generate_cpp.py
    if [ $? -ne 0 ]; then
        echo "❌ C++ generation failed!"
        exit 1
    fi
    echo "✅ C++ files generated"
fi

# Check if generated files exist
if [ ! -f "generated/riscv_isa_generated.h" ] || [ ! -f "generated/test_shader_integration.py" ]; then
    echo "Generated files not found. Use --generate to create them first."
    exit 1
fi

# Copy to shader system if requested
if [ "$COPY" = true ]; then
    echo "Copying generated headers to shader system include directory..."
    cp generated/riscv_isa_generated.h ../shader_system/include/
    if [ $? -ne 0 ]; then
        echo "❌ Failed to copy to shader system!"
        exit 1
    fi
    echo "✅ Copied riscv_isa_generated.h to shader system"
fi

# Run Python integration test
echo "Running Python integration test..."
python3 generated/test_shader_integration.py
if [ $? -ne 0 ]; then
    echo "❌ Python integration test failed!"
    exit 1
fi
echo "✅ Python integration test passed!"

# Build shader system tests if requested
if [ "$BUILD" = true ]; then
    echo "Building shader system tests..."
    cd ../shader_system && make test_riscv_decode
    if [ $? -ne 0 ]; then
        echo "❌ Shader system build failed!"
        exit 1
    fi
    echo "✅ Shader system tests built successfully"
    cd - > /dev/null
fi

echo "✅ Integration test completed successfully!"