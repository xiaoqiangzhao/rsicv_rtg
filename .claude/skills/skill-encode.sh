#!/bin/bash
# Skill: Test instruction encoding/decoding
# Usage: skill-encode [options]
# Options:
#   -n, --count NUM    Number of instructions to test (default: 100)
#   -s, --seed NUM     Random seed for reproducibility (default: 123)
#   --all-formats       Test all instruction formats (R, I, S, B, U, J)
#   --specific FORMAT   Test specific format (r, i, s, b, u, j, special)
#   --verbose          Print detailed output
#   --help             Show this help

COUNT=100
SEED=123
ALL_FORMATS=false
SPECIFIC=""
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--count)
            COUNT="$2"
            shift 2
            ;;
        -s|--seed)
            SEED="$2"
            shift 2
            ;;
        --all-formats)
            ALL_FORMATS=true
            shift
            ;;
        --specific)
            SPECIFIC="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: skill-encode [options]"
            echo "Options:"
            echo "  -n, --count NUM    Number of instructions to test (default: 100)"
            echo "  -s, --seed NUM     Random seed for reproducibility (default: 123)"
            echo "  --all-formats       Test all instruction formats (R, I, S, B, U, J)"
            echo "  --specific FORMAT   Test specific format (r, i, s, b, u, j, special)"
            echo "  --verbose          Print detailed output"
            echo "  --help             Show this help"
            echo ""
            echo "Tests instruction encoding/decoding by:"
            echo "  1. Generating random instructions"
            echo "  2. Encoding them to 32-bit binary/hex"
            echo "  3. Decoding them back to assembly"
            echo "  4. Verifying round-trip correctness"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Testing instruction encoding/decoding..."
echo "  Count: $COUNT"
echo "  Seed: $SEED"
echo "  All formats: $ALL_FORMATS"
echo "  Specific format: ${SPECIFIC:-none}"
echo "  Verbose: $VERBOSE"
echo ""

# Build arguments
ARGS="--count $COUNT --seed $SEED"
if [ "$ALL_FORMATS" = true ]; then
    ARGS="$ARGS --all-formats"
elif [ -n "$SPECIFIC" ]; then
    ARGS="$ARGS --specific $SPECIFIC"
fi
if [ "$VERBOSE" = true ]; then
    ARGS="$ARGS --verbose"
fi

# Run the test
SCRIPT_DIR="$(dirname "$0")"
python3 "$SCRIPT_DIR/test_encoding.py" $ARGS
EXIT_CODE=$?

# Check result
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All encoding/decoding tests passed!"
    exit 0
else
    echo "❌ Encoding/decoding tests failed!"
    exit 1
fi