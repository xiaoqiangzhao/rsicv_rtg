#!/bin/bash
# Quick example script for riscv_rtg

echo "=== RISC-V Random Instruction Generator Demo ==="
echo

echo "1. Generating 5 random instructions (hex):"
python3 generator.py -n 5
echo

echo "2. Generating 3 instructions in assembly format:"
python3 generator.py -n 3 -f asm
echo

echo "3. Generating 2 R-type instructions only:"
python3 generator.py --by-format R -n 2 -f asm
echo

echo "4. Generating 3 instructions in hex+asm format:"
python3 generator.py -n 3 -f hexasm
echo

echo "5. Generating 3 instructions with PC comments (base address 0x1000):"
python3 generator.py -n 3 --pc-comments --base-address 0x1000 -f asm
echo

echo "6. List all available instructions:"
python3 generator.py --list-instructions | head -10
echo "..."
echo

echo "7. Weighted generation (favor R-type, reduce I-type):"
python3 generator.py -n 5 --weight-r 2.5 --weight-i 0.7 -f asm
echo

echo "8. Load/store offset range control:"
python3 generator.py --pattern load-store --load-store-offset-min -50 --load-store-offset-max 50 -f asm
echo
echo "9. Reproducible generation with seed 999:"
python3 generator.py -n 2 -s 999 -f all
echo

echo "10. Configuration file example:"
python3 generator.py --config example_config.yaml -n 3 -f asm
echo

echo "=== Demo complete ==="