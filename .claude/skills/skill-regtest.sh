#!/bin/bash
# Skill: Test register range control feature
# Usage: skill-regtest [options]
# Options:
#   --rd-min N    Minimum destination register (default: 5)
#   --rd-max N    Maximum destination register (default: 7)
#   --rs1-min N   Minimum source register 1 (default: 6)
#   --rs1-max N   Maximum source register 1 (default: 6)
#   --rs2-min N   Minimum source register 2 (default: 7)
#   --rs2-max N   Maximum source register 2 (default: 7)
#   --all         Test all register ranges 0-31
#   --help        Show this help

RD_MIN=5
RD_MAX=7
RS1_MIN=6
RS1_MAX=6
RS2_MIN=7
RS2_MAX=7
COUNT=5
PATTERN="random"

while [[ $# -gt 0 ]]; do
    case $1 in
        --rd-min)
            RD_MIN="$2"
            shift 2
            ;;
        --rd-max)
            RD_MAX="$2"
            shift 2
            ;;
        --rs1-min)
            RS1_MIN="$2"
            shift 2
            ;;
        --rs1-max)
            RS1_MAX="$2"
            shift 2
            ;;
        --rs2-min)
            RS2_MIN="$2"
            shift 2
            ;;
        --rs2-max)
            RS2_MAX="$2"
            shift 2
            ;;
        --all)
            RD_MIN=0
            RD_MAX=31
            RS1_MIN=0
            RS1_MAX=31
            RS2_MIN=0
            RS2_MAX=31
            shift
            ;;
        --help)
            echo "Usage: skill-regtest [options]"
            echo "Test the register range control feature added to riscv_rtg."
            echo ""
            echo "Options:"
            echo "  --rd-min N    Minimum destination register (default: 5)"
            echo "  --rd-max N    Maximum destination register (default: 7)"
            echo "  --rs1-min N   Minimum source register 1 (default: 6)"
            echo "  --rs1-max N   Maximum source register 1 (default: 6)"
            echo "  --rs2-min N   Minimum source register 2 (default: 7)"
            echo "  --rs2-max N   Maximum source register 2 (default: 7)"
            echo "  --all         Test all register ranges 0-31"
            echo "  --help        Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Testing register range control feature:"
echo "  Destination registers (rd): $RD_MIN-$RD_MAX"
echo "  Source register 1 (rs1):    $RS1_MIN-$RS1_MAX"
echo "  Source register 2 (rs2):    $RS2_MIN-$RS2_MAX"
echo ""

echo "Generating $COUNT instructions with these register ranges:"
python3 -m generator -n "$COUNT" -f asm --pattern "$PATTERN" \
    --rd-min "$RD_MIN" --rd-max "$RD_MAX" \
    --rs1-min "$RS1_MIN" --rs1-max "$RS1_MAX" \
    --rs2-min "$RS2_MIN" --rs2-max "$RS2_MAX" \
    --seed 42

echo ""
echo "Testing with load-store pattern:"
python3 -m generator -n 4 -f asm --pattern "load-store" \
    --rd-min "$RD_MIN" --rd-max "$RD_MAX" \
    --rs1-min "$RS1_MIN" --rs1-max "$RS1_MAX" \
    --rs2-min "$RS2_MIN" --rs2-max "$RS2_MAX" \
    --seed 42

echo ""
echo "Testing with RAW hazard pattern:"
python3 -m generator -n 2 -f asm --pattern "raw" \
    --rd-min "$RD_MIN" --rd-max "$RD_MAX" \
    --rs1-min "$RS1_MIN" --rs1-max "$RS1_MAX" \
    --rs2-min "$RS2_MIN" --rs2-max "$RS2_MAX" \
    --seed 42