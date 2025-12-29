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

echo "4. List all available instructions:"
python3 generator.py --list-instructions | head -10
echo "..."
echo

echo "5. Reproducible generation with seed 999:"
python3 generator.py -n 2 -s 999 -f all
echo

echo "=== Demo complete ==="