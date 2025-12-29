#!/usr/bin/env python3
"""
RISC-V Random Instruction Generator CLI.
"""

import argparse
import random
import sys
from typing import List, Tuple
from riscv_isa import RISCVISA, InstructionFormat, format_binary, format_hex
from patterns import PatternGenerator


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
        "-f", "--format", choices=["hex", "bin", "asm", "hexasm", "all"], default="hex",
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
        "--pc-comments", action="store_true",
        help="Include PC (program counter) comments in assembly output"
    )
    parser.add_argument(
        "--base-address", type=lambda x: int(x, 0), default=0x0,
        help="Base address for PC comments (default: 0x0)"
    )
    parser.add_argument(
        "--list-instructions", action="store_true",
        help="List all available instructions and exit"
    )
    parser.add_argument(
        "--by-format", type=str, choices=["R", "I", "S", "B", "U", "J"],
        help="Only generate instructions of specified format"
    )
    # Weight arguments for instruction formats
    parser.add_argument(
        "--weight-r", type=float, default=1.0,
        help="Weight for R-type instructions (default: 1.0)"
    )
    parser.add_argument(
        "--weight-i", type=float, default=1.0,
        help="Weight for I-type instructions (default: 1.0)"
    )
    parser.add_argument(
        "--weight-s", type=float, default=1.0,
        help="Weight for S-type instructions (default: 1.0)"
    )
    parser.add_argument(
        "--weight-b", type=float, default=1.0,
        help="Weight for B-type instructions (default: 1.0)"
    )
    parser.add_argument(
        "--weight-u", type=float, default=1.0,
        help="Weight for U-type instructions (default: 1.0)"
    )
    parser.add_argument(
        "--weight-j", type=float, default=1.0,
        help="Weight for J-type instructions (default: 1.0)"
    )
    parser.add_argument(
        "--weight-special", type=float, default=1.0,
        help="Weight for special instructions (ecall, ebreak) (default: 1.0)"
    )
    # Pattern generation arguments
    parser.add_argument(
        "--pattern", type=str, choices=["random", "load-store", "raw", "war", "waw", "basic-block", "mixed"],
        default="random",
        help="Instruction pattern to generate (default: random)"
    )
    parser.add_argument(
        "--pattern-density", type=float, default=0.3,
        help="Density of patterns in mixed generation (0.0-1.0) (default: 0.3)"
    )
    # Address range arguments for load/store instructions
    parser.add_argument(
        "--load-store-offset-min", type=lambda x: int(x, 0), default=-2048,
        help="Minimum offset for load/store instructions (default: -2048)"
    )
    parser.add_argument(
        "--load-store-offset-max", type=lambda x: int(x, 0), default=2047,
        help="Maximum offset for load/store instructions (default: 2047)"
    )

    args = parser.parse_args()

    # Handle list-instructions
    if args.list_instructions:
        isa = RISCVISA(load_store_offset_min=args.load_store_offset_min,
                       load_store_offset_max=args.load_store_offset_max)
        print(f"Total instructions: {len(isa.instructions)}")
        for instr in isa.instructions:
            print(f"  {instr.name:8} {instr.format.value:4} opcode={instr.opcode:07b}")
        return 0

    # Generate instructions
    if args.seed is not None:
        random.seed(args.seed)

    isa = RISCVISA(load_store_offset_min=args.load_store_offset_min,
                   load_store_offset_max=args.load_store_offset_max)

    # Apply weights based on command-line arguments
    if args.weight_r != 1.0:
        isa.set_weight_by_format(InstructionFormat.R, args.weight_r)
    if args.weight_i != 1.0:
        isa.set_weight_by_format(InstructionFormat.I, args.weight_i)
    if args.weight_s != 1.0:
        isa.set_weight_by_format(InstructionFormat.S, args.weight_s)
    if args.weight_b != 1.0:
        isa.set_weight_by_format(InstructionFormat.B, args.weight_b)
    if args.weight_u != 1.0:
        isa.set_weight_by_format(InstructionFormat.U, args.weight_u)
    if args.weight_j != 1.0:
        isa.set_weight_by_format(InstructionFormat.J, args.weight_j)

    # Apply special instruction weights (ecall, ebreak)
    if args.weight_special != 1.0:
        for name in ['ecall', 'ebreak']:
            try:
                isa.set_weight_by_name(name, args.weight_special)
            except ValueError:
                pass  # Instruction might not exist (shouldn't happen)

    # Create pattern generator
    pattern_gen = PatternGenerator(isa)

    # Filter by format if requested
    if args.by_format:
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

    # Generate based on pattern
    results = []

    if args.pattern == "random":
        # Use existing random generation with format filtering
        for _ in range(args.count):
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = instr.generate_random()
            results.append((encoded, asm))

    elif args.pattern == "load-store":
        # Generate load-store pairs
        pairs_needed = args.count // 2
        extra_needed = args.count % 2

        for _ in range(pairs_needed):
            pair = pattern_gen.generate_load_store_pair()
            results.extend(pair)

        # Add extra random instructions if count is odd
        for _ in range(extra_needed):
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = instr.generate_random()
            results.append((encoded, asm))

    elif args.pattern == "raw":
        # Generate RAW hazard pairs
        pairs_needed = args.count // 2
        extra_needed = args.count % 2

        for _ in range(pairs_needed):
            pair = pattern_gen.generate_raw_hazard()
            results.extend(pair)

        for _ in range(extra_needed):
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = instr.generate_random()
            results.append((encoded, asm))

    elif args.pattern == "war":
        # Generate WAR hazard pairs
        pairs_needed = args.count // 2
        extra_needed = args.count % 2

        for _ in range(pairs_needed):
            pair = pattern_gen.generate_war_hazard()
            results.extend(pair)

        for _ in range(extra_needed):
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = instr.generate_random()
            results.append((encoded, asm))

    elif args.pattern == "waw":
        # Generate WAW hazard pairs
        pairs_needed = args.count // 2
        extra_needed = args.count % 2

        for _ in range(pairs_needed):
            pair = pattern_gen.generate_waw_hazard()
            results.extend(pair)

        for _ in range(extra_needed):
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = instr.generate_random()
            results.append((encoded, asm))

    elif args.pattern == "basic-block":
        # Generate basic block
        block = pattern_gen.generate_basic_block(args.count)
        results.extend(block)

    elif args.pattern == "mixed":
        # Generate mixed patterns
        patterns_list = ['load_store', 'raw', 'war', 'waw']
        mixed = pattern_gen.generate_mixed_patterns(args.count, patterns_list, density=args.pattern_density)
        results.extend(mixed)

    # Ensure we have exactly count instructions (in case pattern generation gave wrong number)
    results = results[:args.count]

    # Output
    output_lines = []
    current_address = args.base_address

    for encoded, asm in results:
        # Add PC comment if requested and format includes assembly
        asm_with_pc = asm
        if args.pc_comments and args.format in ["asm", "hexasm", "all"]:
            asm_with_pc = f"{asm}  # 0x{current_address:08x}"

        if args.format == "hex":
            output_lines.append(format_hex(encoded))
        elif args.format == "bin":
            output_lines.append(format_binary(encoded))
        elif args.format == "asm":
            output_lines.append(asm_with_pc)
        elif args.format == "hexasm":
            output_lines.append(f"{format_hex(encoded)} {asm_with_pc}")
        elif args.format == "all":
            output_lines.append(f"{format_hex(encoded)} {format_binary(encoded)} {asm_with_pc}")

        # Increment PC for next instruction (4 bytes per instruction)
        current_address += 4

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