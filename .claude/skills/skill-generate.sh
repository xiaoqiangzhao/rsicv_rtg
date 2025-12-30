#!/bin/bash
# Skill: Generate RISC-V instructions
# Usage: skill-generate [options]
# Options:
#   -n, --count NUM    Number of instructions (default: 10)
#   -f, --format FMT   Output format: hex, bin, asm, hexasm, all (default: asm)
#   -p, --pattern PAT  Pattern: random, load-store, raw, war, waw, mixed (default: random)
#   --regtest          Test register ranges: rd=5-7, rs1=6-6, rs2=7-7
#   --help             Show this help

COUNT=10
FORMAT="asm"
PATTERN="random"
REGTEST=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--count)
            COUNT="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -p|--pattern)
            PATTERN="$2"
            shift 2
            ;;
        --regtest)
            REGTEST=true
            shift
            ;;
        --help)
            echo "Usage: skill-generate [options]"
            echo "Options:"
            echo "  -n, --count NUM    Number of instructions (default: 10)"
            echo "  -f, --format FMT   Output format: hex, bin, asm, hexasm, all (default: asm)"
            echo "  -p, --pattern PAT  Pattern: random, load-store, raw, war, waw, mixed (default: random)"
            echo "  --regtest          Test register ranges: rd=5-7, rs1=6-6, rs2=7-7"
            echo "  --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Generating $COUNT instructions in $FORMAT format with $PATTERN pattern..."

if [ "$REGTEST" = true ]; then
    echo "Testing register ranges: rd=5-7, rs1=6-6, rs2=7-7"
    python3 -m generator -n "$COUNT" -f "$FORMAT" --pattern "$PATTERN" \
        --rd-min 5 --rd-max 7 --rs1-min 6 --rs1-max 6 --rs2-min 7 --rs2-max 7
else
    python3 -m generator -n "$COUNT" -f "$FORMAT" --pattern "$PATTERN"
fi