#!/bin/bash
# Skill: Test RV32M multiply/divide instruction generation
# Usage: skill-test-rv32m [options]
# Options:
#   -c, --count NUM    Number of instructions to generate (default: 10000)
#   -s, --seed NUM     Random seed for reproducibility (default: 42)
#   -v, --verbose      Print detailed output
#   --help             Show this help

COUNT=10000
SEED=42
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--count)
            COUNT="$2"
            shift 2
            ;;
        -s|--seed)
            SEED="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: skill-test-rv32m [options]"
            echo "Options:"
            echo "  -c, --count NUM    Number of instructions to generate (default: 10000)"
            echo "  -s, --seed NUM     Random seed for reproducibility (default: 42)"
            echo "  -v, --verbose      Print detailed output"
            echo "  --help             Show this help"
            echo ""
            echo "Tests RV32M multiply/divide instruction generation:"
            echo "  - Verifies all 8 RV32M instructions are loaded"
            echo "  - Checks encoding (opcode, funct3, funct7)"
            echo "  - Validates generation frequency"
            echo "  - Tests random instruction generation"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Testing RV32M instruction generation..."
echo "  Count: $COUNT"
echo "  Seed: $SEED"
echo "  Verbose: $VERBOSE"
echo ""

# Build command
CMD="python3 $(dirname "$0")/test_rv32m.py --count $COUNT --seed $SEED"
if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

# Run test
if $CMD; then
    echo "✅ RV32M test passed!"
    exit 0
else
    echo "❌ RV32M test failed!"
    exit 1
fi