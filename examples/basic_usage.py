#!/usr/bin/env python3
"""
Basic usage examples for riscv_rtg.
"""

import os
import sys

# Add parent directory to path so we can import riscv_isa
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from riscv_isa import RISCVISA, InstructionFormat, format_hex, format_binary


def example1():
    """Generate and display random instructions."""
    print("=== Example 1: Basic Generation ===")
    isa = RISCVISA()
    results = isa.generate_random(5)

    for i, (encoded, asm) in enumerate(results):
        print(f"{i+1:2d}. {format_hex(encoded)} {format_binary(encoded)} {asm}")


def example2():
    """Generate instructions of specific format."""
    print("\n=== Example 2: R-type Instructions Only ===")
    isa = RISCVISA()
    r_type = isa.get_instructions_by_format(InstructionFormat.R)

    print(f"Found {len(r_type)} R-type instructions")
    for instr in r_type[:5]:  # Show first 5
        encoded, asm = instr.generate_random()
        print(f"  {instr.name}: {asm}")


def example3():
    """Reproducible generation with seed."""
    print("\n=== Example 3: Reproducible Generation ===")

    import random
    seed = 12345

    random.seed(seed)
    isa1 = RISCVISA()
    results1 = isa1.generate_random(3)

    random.seed(seed)
    isa2 = RISCVISA()
    results2 = isa2.generate_random(3)

    print("First run:")
    for enc, asm in results1:
        print(f"  {format_hex(enc)} {asm}")

    print("Second run (same seed):")
    for enc, asm in results2:
        print(f"  {format_hex(enc)} {asm}")

    print("Results are identical:", results1 == results2)


def example4():
    """Generate large batch and save to file."""
    print("\n=== Example 4: Batch Generation ===")
    isa = RISCVISA()

    # Generate 1000 instructions
    print("Generating 1000 instructions...")
    results = isa.generate_random(1000)

    # Count instruction types
    from collections import Counter
    type_counter = Counter()
    for instr in isa.instructions:
        type_counter[instr.format.value] += 1

    print("Instruction format distribution:")
    for fmt, count in sorted(type_counter.items()):
        print(f"  {fmt}: {count}")

    # Save to file
    with open('generated_instructions.txt', 'w') as f:
        for encoded, asm in results:
            f.write(f"{format_hex(encoded)} {asm}\n")

    print("Saved to 'generated_instructions.txt'")


if __name__ == '__main__':
    example1()
    example2()
    example3()
    example4()

    print("\n=== Done ===")