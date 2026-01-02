#!/usr/bin/env python3
"""Test RV32M instruction generation for skill-test-rv32m.sh."""

import sys
import os
import random

# Add parent directory to path to import riscv_rtg modules
# File is in .claude/skills/, need to go up 3 levels to project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

from riscv_rtg.isa.riscv_isa import RISCVISA

def test_rv32m_generation(count=10000, seed=42, verbose=False):
    """Test RV32M instruction generation.

    Args:
        count: Number of instructions to generate
        seed: Random seed for reproducibility
        verbose: Print detailed output

    Returns:
        bool: True if all tests pass
    """
    random.seed(seed)
    isa = RISCVISA()

    # Find RV32M instructions
    rv32m_names = ['mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu', 'rem', 'remu']
    rv32m_instructions = [instr for instr in isa.instructions if instr.name in rv32m_names]

    if verbose:
        print(f"Total instructions: {len(isa.instructions)}")
        print(f"RV32M instructions found: {len(rv32m_instructions)}")
        for instr in rv32m_instructions:
            print(f"  {instr.name}: opcode={instr.opcode:#010b}, funct3={instr.funct3}, funct7={instr.funct7}")

    # Generate random instructions and count RV32M occurrences
    samples = count
    counts = {}
    for _ in range(samples):
        instr = isa.get_random_instruction()
        counts[instr.name] = counts.get(instr.name, 0) + 1

    # Calculate RV32M statistics
    rv32m_counts = {name: counts.get(name, 0) for name in rv32m_names}
    total_rv32m = sum(rv32m_counts.values())
    rv32m_percentage = total_rv32m / samples * 100

    if verbose:
        print(f"\nGenerated {samples} random instructions:")
        print(f"Total RV32M instructions: {total_rv32m} ({rv32m_percentage:.2f}%)")
        print("\nIndividual RV32M instruction counts:")
        for name in rv32m_names:
            count_val = rv32m_counts[name]
            percentage = count_val / samples * 100
            print(f"  {name}: {count_val} ({percentage:.2f}%)")

    # Expected: each RV32M instruction should appear roughly 1/47 of the time
    # (47 total instructions, 8 RV32M instructions)
    expected_percentage = 8 / 47 * 100  # ~17.02%

    # Check basic requirements
    errors = []

    # 1. All RV32M instructions should be present in ISA
    if len(rv32m_instructions) != 8:
        errors.append(f"Expected 8 RV32M instructions, found {len(rv32m_instructions)}")

    # 2. RV32M instructions should appear with reasonable frequency
    # Allow some variation due to randomness
    lower_bound = expected_percentage * 0.5  # 50% of expected
    upper_bound = expected_percentage * 1.5  # 150% of expected

    if not (lower_bound <= rv32m_percentage <= upper_bound):
        errors.append(f"RV32M frequency {rv32m_percentage:.2f}% outside expected range [{lower_bound:.2f}%, {upper_bound:.2f}%]")

    # 3. Each RV32M instruction should appear at least once in large sample
    if samples >= 1000:
        for name in rv32m_names:
            if rv32m_counts[name] == 0:
                errors.append(f"RV32M instruction '{name}' never appeared in {samples} samples")

    # 4. Verify encoding for each RV32M instruction
    for instr in rv32m_instructions:
        encoded, asm = instr.generate_random()
        # Check opcode matches OP (0b0110011)
        opcode = encoded & 0x7f
        if opcode != instr.opcode:
            errors.append(f"{instr.name}: opcode mismatch {opcode:#010b} vs {instr.opcode:#010b}")

        # Check funct7 matches MULDIV (0b0000001) for RV32M
        funct7 = (encoded >> 25) & 0x7f
        if funct7 != instr.funct7:
            errors.append(f"{instr.name}: funct7 mismatch {funct7:#09b} vs {instr.funct7:#09b}")

    # Report results
    if errors:
        if verbose:
            print("\n❌ RV32M test failed with errors:")
            for error in errors:
                print(f"  - {error}")
        return False
    else:
        if verbose:
            print(f"\n✅ RV32M test passed!")
            print(f"  - Found all 8 RV32M instructions")
            print(f"  - RV32M frequency: {rv32m_percentage:.2f}% (expected ~{expected_percentage:.2f}%)")
            print(f"  - All encodings verified")
        return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test RV32M instruction generation")
    parser.add_argument("--count", type=int, default=10000,
                       help="Number of instructions to generate (default: 10000)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed (default: 42)")
    parser.add_argument("--verbose", action="store_true",
                       help="Print detailed output")

    args = parser.parse_args()

    success = test_rv32m_generation(
        count=args.count,
        seed=args.seed,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()