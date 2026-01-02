#!/usr/bin/env python3
"""Test instruction encoding/decoding for skill-encode.sh."""

import sys
import os
import random

# Add parent directory to path to import riscv_rtg modules
# File is in .claude/skills/, need to go up 3 levels to project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

from riscv_rtg.isa.riscv_isa import RISCVISA

def test_encoding(count=100, seed=123, specific_format=None, all_formats=False, verbose=False):
    """Test instruction encoding/decoding.

    Args:
        count: Number of instructions to test
        seed: Random seed
        specific_format: Test specific format (r, i, s, b, u, j, special)
        all_formats: Test all formats
        verbose: Print detailed output

    Returns:
        bool: True if all tests pass
    """
    random.seed(seed)
    isa = RISCVISA()

    if all_formats:
        formats = ['r', 'i', 's', 'b', 'u', 'j', 'special']
    elif specific_format:
        formats = [specific_format]
    else:
        formats = [None]  # None means random from all formats

    errors = 0

    for fmt in formats:
        if verbose:
            if fmt:
                print(f"Testing {fmt.upper()}-type instructions...")
            else:
                print("Testing random instructions...")

        for i in range(count):
            if fmt:
                instr = isa.get_random_instruction_by_format(fmt)
            else:
                instr = isa.get_random_instruction()

            encoded, assembly = instr.generate_random()

            # Decode by finding instruction with matching encoding
            # Simple approach: check each instruction's encoding pattern
            decoded_instr = None
            for test_instr in isa.instructions:
                # Check if opcode matches
                if (encoded & 0x7f) != test_instr.opcode:
                    continue

                # Check if funct3 matches (for R/I/S/B formats)
                if hasattr(test_instr, 'funct3') and test_instr.funct3 is not None:
                    if ((encoded >> 12) & 0x7) != test_instr.funct3:
                        continue

                # Check if funct7 matches (for R-type)
                if hasattr(test_instr, 'funct7') and test_instr.funct7 is not None:
                    if ((encoded >> 25) & 0x7f) != test_instr.funct7:
                        continue

                # Found matching instruction
                decoded_instr = test_instr
                break

            if decoded_instr is None:
                print(f"❌ Failed to decode: {hex(encoded)}")
                errors += 1
            elif decoded_instr.name != instr.name:
                print(f"❌ Decoding mismatch: {instr.name} -> {decoded_instr.name}")
                print(f"   Encoding: {hex(encoded)}")
                errors += 1
            else:
                if verbose:
                    print(f"✅ {instr.name}: {hex(encoded)} -> {assembly}")

    print(f"\nTotal errors: {errors}")
    return errors == 0

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test instruction encoding/decoding")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of instructions to test (default: 100)")
    parser.add_argument("--seed", type=int, default=123,
                       help="Random seed (default: 123)")
    parser.add_argument("--all-formats", action="store_true",
                       help="Test all instruction formats")
    parser.add_argument("--specific", type=str,
                       help="Test specific format (r, i, s, b, u, j, special)")
    parser.add_argument("--verbose", action="store_true",
                       help="Print detailed output")

    args = parser.parse_args()

    success = test_encoding(
        count=args.count,
        seed=args.seed,
        specific_format=args.specific,
        all_formats=args.all_formats,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()