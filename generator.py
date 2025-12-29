#!/usr/bin/env python3
"""
RISC-V Random Instruction Generator CLI.
"""

import argparse
import random
import sys
from typing import List, Tuple
from riscv_isa import RISCVISA, format_binary, format_hex


def generate_instructions(count: int, output_format: str, seed: int = None) -> List[Tuple[int, str]]:
    """Generate random instructions."""
    if seed is not None:
        random.seed(seed)

    isa = RISCVISA()
    return isa.generate_random(count)


def main():
    parser = argparse.ArgumentParser(
        description="Generate random RISC-V instructions",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-n", "--count", type=int, default=10,
        help="Number of instructions to generate"
    )
    parser.add_argument(
        "-f", "--format", choices=["hex", "bin", "asm", "all"], default="hex",
        help="Output format"
    )
    parser.add_argument(
        "-s", "--seed", type=int, default=None,
        help="Random seed for reproducible generation"
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--list-instructions", action="store_true",
        help="List all available instructions and exit"
    )
    parser.add_argument(
        "--by-format", type=str, choices=["R", "I", "S", "B", "U", "J"],
        help="Only generate instructions of specified format"
    )

    args = parser.parse_args()

    # Handle list-instructions
    if args.list_instructions:
        isa = RISCVISA()
        print(f"Total instructions: {len(isa.instructions)}")
        for instr in isa.instructions:
            print(f"  {instr.name:8} {instr.format.value:4} opcode={instr.opcode:07b}")
        return 0

    # Generate instructions
    if args.seed is not None:
        random.seed(args.seed)

    isa = RISCVISA()

    # Filter by format if requested
    if args.by_format:
        from riscv_isa import InstructionFormat
        fmt_map = {"R": InstructionFormat.R, "I": InstructionFormat.I,
                   "S": InstructionFormat.S, "B": InstructionFormat.B,
                   "U": InstructionFormat.U, "J": InstructionFormat.J}
        fmt = fmt_map[args.by_format]
        instructions = isa.get_instructions_by_format(fmt)
        if not instructions:
            print(f"No instructions found for format {args.by_format}", file=sys.stderr)
            return 1
    else:
        instructions = isa.instructions

    # Generate
    results = []
    for _ in range(args.count):
        instr = random.choice(instructions)
        encoded, asm = instr.generate_random()
        results.append((encoded, asm))

    # Output
    output_lines = []
    for encoded, asm in results:
        if args.format == "hex":
            output_lines.append(format_hex(encoded))
        elif args.format == "bin":
            output_lines.append(format_binary(encoded))
        elif args.format == "asm":
            output_lines.append(asm)
        elif args.format == "all":
            output_lines.append(f"{format_hex(encoded)} {format_binary(encoded)} {asm}")

    output_text = "\n".join(output_lines)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text + "\n")
        print(f"Generated {args.count} instructions to {args.output}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())