#!/bin/bash
# Skill: Check consistency between Python and C++ instruction definitions
# Usage: skill-consistency [options]
# Options:
#   --generate     Generate C++ files first for comparison
#   --check-yaml   Check YAML definition consistency
#   --check-enums  Check enum value consistency
#   --check-all    Check all consistency aspects
#   --verbose      Print detailed output
#   --help         Show this help

GENERATE=false
CHECK_YAML=false
CHECK_ENUMS=false
CHECK_ALL=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --generate)
            GENERATE=true
            shift
            ;;
        --check-yaml)
            CHECK_YAML=true
            shift
            ;;
        --check-enums)
            CHECK_ENUMS=true
            shift
            ;;
        --check-all)
            CHECK_ALL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: skill-consistency [options]"
            echo "Options:"
            echo "  --generate     Generate C++ files first for comparison"
            echo "  --check-yaml   Check YAML definition consistency"
            echo "  --check-enums  Check enum value consistency"
            echo "  --check-all    Check all consistency aspects"
            echo "  --verbose      Print detailed output"
            echo "  --help         Show this help"
            echo ""
            echo "Checks consistency between:"
            echo "  1. YAML definitions (rv32i.yaml)"
            echo "  2. Python enums (enums.py)"
            echo "  3. C++ header (riscv_isa.h)"
            echo "  4. Generated C++ files (riscv_isa_generated.h)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Checking consistency between Python and C++ instruction definitions..."
echo "  Generate C++ files: $GENERATE"
echo "  Check YAML: $CHECK_YAML"
echo "  Check enums: $CHECK_ENUMS"
echo "  Check all: $CHECK_ALL"
echo "  Verbose: $VERBOSE"
echo ""

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

# Build arguments for consistency check
ARGS=""
if [ "$CHECK_YAML" = true ]; then
    ARGS="$ARGS --check-yaml"
fi
if [ "$CHECK_ENUMS" = true ]; then
    ARGS="$ARGS --check-enums"
fi
if [ "$CHECK_ALL" = true ]; then
    ARGS="$ARGS --check-all"
fi
if [ "$VERBOSE" = true ]; then
    ARGS="$ARGS --verbose"
fi

# If no check flags specified, default to --check-all
if [ -z "$ARGS" ]; then
    ARGS="--check-all"
    echo "No check flags specified, using --check-all"
fi

# Run consistency check
SCRIPT_DIR="$(dirname "$0")"
python3 "$SCRIPT_DIR/test_consistency.py" $ARGS
EXIT_CODE=$?

# Check result
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All consistency checks passed!"
    exit 0
else
    echo "❌ Consistency checks failed!"
    exit 1
fi