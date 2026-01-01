#!/usr/bin/env python3
"""
RISC-V Random Instruction Generator CLI.
"""

import argparse
import random
import sys
import yaml
from typing import List, Tuple, Optional
from riscv_rtg.isa.riscv_isa import RISCVISA, InstructionFormat, format_binary, format_hex
from .patterns import PatternGenerator, SemanticState, CommentGenerator
from .sequence_patterns import SequencePatternLoader, SequencePatternGenerator


def parse_load_store_ranges(ranges_spec: Optional[str]) -> Optional[List[Tuple[int, int]]]:
    """Parse load/store offset ranges specification.

    Args:
        ranges_spec: Comma-separated list of "base:size" pairs, or None.

    Returns:
        List of (base, size) tuples, or None if ranges_spec is None.

    Raises:
        ValueError: If format is invalid or size <= 0.
    """
    if ranges_spec is None:
        return None

    ranges = []
    for part in ranges_spec.split(','):
        part = part.strip()
        if not part:
            continue
        if ':' not in part:
            raise ValueError(f"Range '{part}' must be in format 'base:size'")
        base_str, size_str = part.split(':', 1)
        try:
            base = int(base_str, 0)  # Supports hex (0x) and decimal
            size = int(size_str, 0)
        except ValueError as e:
            raise ValueError(f"Invalid integer in range '{part}': {e}")
        if size <= 0:
            raise ValueError(f"Range size must be positive, got size={size} in '{part}'")
        ranges.append((base, size))
    return ranges


def convert_load_store_ranges(value) -> Optional[List[Tuple[int, int]]]:
    """Convert load_store_ranges config value to list of tuples.

    Handles:
    - None -> None
    - String (comma-separated) -> parse_load_store_ranges
    - List of strings -> each string parsed as "base:size"
    - List of lists -> each inner list [base, size]

    Returns:
        List of (base, size) tuples, or None.

    Raises:
        ValueError: If format is invalid.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return parse_load_store_ranges(value)
    if isinstance(value, list):
        ranges = []
        for item in value:
            if isinstance(item, str):
                # Expect "base:size"
                if ':' not in item:
                    raise ValueError(f"Range string '{item}' must be in format 'base:size'")
                base_str, size_str = item.split(':', 1)
                base = int(base_str, 0)
                size = int(size_str, 0)
            elif isinstance(item, list) and len(item) == 2:
                base, size = item[0], item[1]
                # Convert to int if they're strings
                if isinstance(base, str):
                    base = int(base, 0)
                if isinstance(size, str):
                    size = int(size, 0)
            else:
                raise ValueError(f"Invalid range item: {item}. Expected string 'base:size' or list [base, size]")
            if size <= 0:
                raise ValueError(f"Range size must be positive, got size={size}")
            ranges.append((base, size))
        return ranges
    raise ValueError(f"Invalid type for load_store_ranges: {type(value)}")


def generate_instructions(count: int, output_format: str, seed: int = None) -> List[Tuple[int, str]]:
    """Generate random instructions."""
    if seed is not None:
        random.seed(seed)

    isa = RISCVISA()
    return isa.generate_random(count)


def load_config(config_path: str) -> dict:
    """Load YAML configuration file and return as dictionary.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary with configuration values

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML syntax is invalid
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in {config_path}: {e}")


def validate_and_convert_config(config: dict) -> dict:
    """Validate config values and convert types to match argparse expectations.

    Handles type conversions for hex strings, floats, and nested weight dictionary.

    Args:
        config: Raw configuration dictionary from YAML

    Returns:
        Validated and converted configuration dictionary
    """
    if not config:
        return {}

    validated = {}

    # Helper for hex/decimal conversion matching argparse's lambda x: int(x, 0)
    def convert_int(value):
        """Convert to int, handling hex strings (0x...) like argparse."""
        if isinstance(value, str):
            return int(value, 0)
        return int(value)

    # Convert known fields
    int_fields = ['count', 'seed', 'base_address',
                  'load_store_offset_min', 'load_store_offset_max',
                  'rd_min', 'rd_max', 'rs1_min', 'rs1_max', 'rs2_min', 'rs2_max']
    float_fields = ['pattern_density']

    for key, value in config.items():
        if value is None:
            # Keep None values (e.g., seed: null)
            validated[key] = None
        elif key == 'weights' and isinstance(value, dict):
            # Convert nested weights dictionary
            validated[key] = {}
            for weight_key, weight_val in value.items():
                if weight_val is not None:
                    validated[key][weight_key] = float(weight_val)
        elif key == 'load_store_ranges' and value is not None:
            # Convert load/store ranges
            validated[key] = convert_load_store_ranges(value)
        elif key in int_fields and value is not None:
            validated[key] = convert_int(value)
        elif key in float_fields and value is not None:
            validated[key] = float(value)
        else:
            # Pass through other values (strings, booleans)
            validated[key] = value

    return validated


def merge_config_with_args(config: dict, args: argparse.Namespace, defaults: dict = None) -> argparse.Namespace:
    """Merge config dictionary with argparse Namespace.

    Precedence: CLI arguments override config values.
    Special handling for nested weights dictionary.

    Args:
        config: Validated configuration dictionary
        args: argparse.Namespace from command-line parsing
        defaults: Dictionary of default values for each argument (optional).
                  If not provided, uses heuristic: assume CLI overrode if value != default.

    Returns:
        Updated argparse.Namespace with merged values
    """
    merged = argparse.Namespace(**vars(args))

    # If defaults not provided, create empty dict
    if defaults is None:
        defaults = {}

    # Flatten weights dictionary to individual weight_* attributes
    if 'weights' in config:
        weights = config.pop('weights')
        for fmt, weight in weights.items():
            attr_name = f'weight_{fmt}'
            if hasattr(merged, attr_name):
                # Check if CLI overrode this weight (i.e., value != default)
                current = getattr(merged, attr_name)
                if current == defaults.get(attr_name, 1.0):
                    setattr(merged, attr_name, weight)

    # Merge other fields
    for key, value in config.items():
        if value is not None and hasattr(merged, key):
            # Check if CLI overrode this field (value != default)
            current = getattr(merged, key)
            if current == defaults.get(key):
                setattr(merged, key, value)

    return merged


def main():
    parser = argparse.ArgumentParser(
        description="Generate random RISC-V instructions",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Configuration file argument (must be first to parse early)
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to YAML configuration file (CLI arguments override config)"
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
        "--pattern", type=str, choices=["random", "load-store", "raw", "war", "waw", "basic-block", "mixed", "loop", "conditional", "memory", "function", "sequence"],
        default="random",
        help="Instruction pattern to generate (default: random)"
    )
    parser.add_argument(
        "--pattern-density", type=float, default=0.3,
        help="Density of patterns in mixed generation (0.0-1.0) (default: 0.3)"
    )
    # Sequence pattern arguments
    parser.add_argument(
        "--sequence-patterns-file", type=str, default=None,
        help="YAML file containing sequence pattern definitions (required for 'sequence' pattern)"
    )
    parser.add_argument(
        "--sequence-patterns", type=str, default=None,
        help="Comma-separated list of sequence pattern names to use (default: use all patterns)"
    )
    parser.add_argument(
        "--sequence-density", type=float, default=0.3,
        help="Density of sequence patterns in generation (0.0-1.0) (default: 0.3)"
    )
    # Semantic correlation arguments
    parser.add_argument(
        "--semantic-correlation", action="store_true", default=False,
        help="Enable semantic correlation in instruction generation"
    )
    parser.add_argument(
        "--semantic-comments", action="store_true", default=False,
        help="Enable semantic comments in output"
    )
    parser.add_argument(
        "--comment-detail", choices=["minimal", "medium", "detailed"], default="medium",
        help="Detail level for semantic comments (default: medium)"
    )
    parser.add_argument(
        "--correlation-types", type=str, default="data,control,memory,function",
        help="Comma-separated list of correlation types: data,control,memory,function (default: all)"
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
    parser.add_argument(
        "--load-store-ranges", type=str, default=None,
        help="Comma-separated list of base:size ranges for load/store offsets (e.g., '-100:200,0x100:0x20'). Use --load-store-ranges='-100:200' or --load-store-ranges \"-100:200\" after -- separator."
    )
    # Register range arguments
    parser.add_argument(
        "--rd-min", type=lambda x: int(x, 0), default=0,
        help="Minimum destination register number (0-31, default: 0)"
    )
    parser.add_argument(
        "--rd-max", type=lambda x: int(x, 0), default=31,
        help="Maximum destination register number (0-31, default: 31)"
    )
    parser.add_argument(
        "--rs1-min", type=lambda x: int(x, 0), default=0,
        help="Minimum source register 1 number (0-31, default: 0)"
    )
    parser.add_argument(
        "--rs1-max", type=lambda x: int(x, 0), default=31,
        help="Maximum source register 1 number (0-31, default: 31)"
    )
    parser.add_argument(
        "--rs2-min", type=lambda x: int(x, 0), default=0,
        help="Minimum source register 2 number (0-31, default: 0)"
    )
    parser.add_argument(
        "--rs2-max", type=lambda x: int(x, 0), default=31,
        help="Maximum source register 2 number (0-31, default: 31)"
    )
    # Hexasm format arguments
    parser.add_argument(
        "--no-hex-comments", action="store_true", default=False,
        help="Disable hex as comment in hexasm format (hex appears as field)"
    )

    # Parse all arguments (known args) to get config path and any CLI arguments
    initial_args, remaining_argv = parser.parse_known_args()

    config = {}
    if initial_args.config:
        try:
            config = load_config(initial_args.config)
            config = validate_and_convert_config(config)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return 1

    # Use initial_args as base (contains CLI values)
    args = initial_args

    # Build dictionary of default values from parser
    defaults = {}
    for action in parser._actions:
        if action.dest != "help" and action.default is not None:
            defaults[action.dest] = action.default

    # Merge config with args (CLI overrides config)
    args = merge_config_with_args(config, args, defaults)

    # Now args contains merged values (CLI overrides config)

    # Parse load/store ranges if specified
    load_store_offset_ranges = None
    if args.load_store_ranges is not None:
        if isinstance(args.load_store_ranges, str):
            load_store_offset_ranges = parse_load_store_ranges(args.load_store_ranges)
        else:
            # Assume it's already a list of tuples (from config)
            load_store_offset_ranges = args.load_store_ranges

    # Handle list-instructions
    if args.list_instructions:
        isa = RISCVISA(load_store_offset_min=args.load_store_offset_min,
                       load_store_offset_max=args.load_store_offset_max,
                       load_store_offset_ranges=load_store_offset_ranges,
                       rd_min=args.rd_min, rd_max=args.rd_max,
                       rs1_min=args.rs1_min, rs1_max=args.rs1_max,
                       rs2_min=args.rs2_min, rs2_max=args.rs2_max)
        print(f"Total instructions: {len(isa.instructions)}")
        for instr in isa.instructions:
            print(f"  {instr.name:8} {instr.format.value:4} opcode={instr.opcode:07b}")
        return 0

    # Generate instructions
    if args.seed is not None:
        random.seed(args.seed)

    isa = RISCVISA(load_store_offset_min=args.load_store_offset_min,
                   load_store_offset_max=args.load_store_offset_max,
                   load_store_offset_ranges=load_store_offset_ranges,
                   rd_min=args.rd_min, rd_max=args.rd_max,
                   rs1_min=args.rs1_min, rs1_max=args.rs1_max,
                   rs2_min=args.rs2_min, rs2_max=args.rs2_max)

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

    # Parse correlation types
    correlation_types_list = [t.strip() for t in args.correlation_types.split(',')] if hasattr(args, 'correlation_types') else []

    # Create semantic state if semantic correlation or comments enabled
    semantic_state = None
    if args.semantic_correlation or args.semantic_comments:
        semantic_state = SemanticState()

    # Set comment detail level (use "none" if semantic comments disabled)
    comment_detail = args.comment_detail if args.semantic_comments else "none"

    # Create pattern generator with semantic features
    pattern_gen = PatternGenerator(isa,
                                   semantic_state=semantic_state,
                                   comment_detail=comment_detail)

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
            encoded, asm = isa.generate_random_instruction(instr)
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
            encoded, asm = isa.generate_random_instruction(instr)
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
            encoded, asm = isa.generate_random_instruction(instr)
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
            encoded, asm = isa.generate_random_instruction(instr)
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
            encoded, asm = isa.generate_random_instruction(instr)
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

    elif args.pattern == "loop":
        # Generate loop pattern
        # Adjust body size to approximate count
        body_size = max(1, args.count - 3)  # init, decrement, branch
        loop_seq = pattern_gen.generate_loop_pattern(iterations=3, body_size=body_size)
        results.extend(loop_seq)
        # Fill remaining with random if needed
        while len(results) < args.count:
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = isa.generate_random_instruction(instr)
            results.append((encoded, asm))

    elif args.pattern == "conditional":
        # Generate conditional pattern
        # Split count between then and else blocks
        then_size = max(1, args.count // 2 - 1)
        else_size = max(1, args.count - then_size - 2)  # branch and jump
        cond_seq = pattern_gen.generate_conditional_pattern(then_size=then_size, else_size=else_size)
        results.extend(cond_seq)
        while len(results) < args.count:
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = isa.generate_random_instruction(instr)
            results.append((encoded, asm))

    elif args.pattern == "memory":
        # Generate memory sequence
        mem_seq = pattern_gen.generate_memory_sequence(size=args.count)
        results.extend(mem_seq)
        # memory sequence already generates exactly size instructions

    elif args.pattern == "function":
        # Generate function sequence
        # Adjust body size to approximate count
        prologue_epilogue_size = 8  # approximate
        body_size = max(1, args.count - prologue_epilogue_size)
        func_seq = pattern_gen.generate_function_sequence(body_size=body_size)
        results.extend(func_seq)
        while len(results) < args.count:
            instr = isa.get_weighted_random_from_list(instructions)
            encoded, asm = isa.generate_random_instruction(instr)
            results.append((encoded, asm))

    elif args.pattern == "sequence":
        # Generate using sequence patterns
        if not args.sequence_patterns_file:
            print("Error: --sequence-patterns-file is required for 'sequence' pattern", file=sys.stderr)
            return 1

        # Load sequence patterns
        try:
            pattern_loader = SequencePatternLoader(args.sequence_patterns_file)
        except Exception as e:
            print(f"Error loading sequence patterns: {e}", file=sys.stderr)
            return 1

        # Parse pattern names if specified
        pattern_names = None
        if args.sequence_patterns:
            pattern_names = [name.strip() for name in args.sequence_patterns.split(',')]

        # Create sequence pattern generator
        seq_pattern_gen = SequencePatternGenerator(isa, pattern_loader, pattern_gen)

        # Generate sequence
        seq_results = seq_pattern_gen.generate_sequence(
            count=args.count,
            pattern_names=pattern_names,
            pattern_density=args.sequence_density
        )
        results.extend(seq_results)

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
            if args.no_hex_comments:
                # Old format: hex as field
                output_lines.append(f"{format_hex(encoded)} {asm_with_pc}")
            else:
                # New format: hex as comment
                output_lines.append(f"{asm_with_pc}  # {format_hex(encoded)}")
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