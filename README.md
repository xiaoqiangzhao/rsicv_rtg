# RISC-V ISA Random Instruction Generator (riscv_rtg)

A Python 3 tool for generating random RISC-V instructions. Useful for testing RISC-V simulators, processors, and educational purposes.

## Features

- Generates random RISC-V RV32I instructions
- Supports all instruction formats: R, I, S, B, U, J
- Output in multiple formats: hexadecimal, binary, assembly, hex+asm, or all
- Filter by instruction format
- Weighted random generation by instruction type
- PC (program counter) comments in assembly output
- Reproducible generation with seed support
- Lists all available instructions

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/riscv_rtg.git
cd riscv_rtg
```

Install as a package:

Note: Configuration file support requires PyYAML, which will be installed automatically.

```bash
pip install -e .
```

Or use directly without installation:

```bash
python -m generator --help
```

## Usage

### Basic generation

Generate 10 random instructions (default):

```bash
python -m generator
```

Generate 5 instructions in assembly format:

```bash
python -m generator -n 5 -f asm
```

### Output formats

- `hex`: Hexadecimal representation (default)
- `bin`: 32-bit binary representation
- `asm`: Assembly syntax
- `hexasm`: Assembly with hexadecimal as comment (useful for debugging). Use `--no-hex-comments` to show hex as a field instead.
- `all`: All of the above (hex, binary, assembly)

Example:

```bash
python -m generator -n 3 -f all
```

### Filter by instruction format

Generate only R-type instructions:

```bash
python -m generator --by-format R
```

Available formats: R, I, S, B, U, J

### Reproducible generation

Use a seed for reproducible output:

```bash
python -m generator -s 42
```

### PC Comments in Assembly

Include program counter (PC) comments in assembly output:

```bash
# Add PC comments with default base address (0x0)
python -m generator --pc-comments -f asm

# Specify custom base address
python -m generator --pc-comments --base-address 0x1000 -f asm

# PC comments work with hexasm and all formats too
python -m generator --pc-comments -f hexasm
```

### Weighted generation

Control the probability of different instruction types using weights:

```bash
# Increase probability of R-type instructions (weight 2.0)
python -m generator --weight-r 2.0

# Decrease probability of I-type instructions (weight 0.5)
python -m generator --weight-i 0.5

# Eliminate R-type instructions (weight 0.0)
python -m generator --weight-r 0.0

# Increase probability of special instructions (ecall, ebreak)
python -m generator --weight-special 5.0

# Combine multiple weights
python -m generator --weight-r 2.0 --weight-i 0.5 --weight-b 1.5
```

Available weight arguments:
- `--weight-r`: R-type instructions
- `--weight-i`: I-type instructions
- `--weight-s`: S-type instructions
- `--weight-b`: B-type instructions
- `--weight-u`: U-type instructions
- `--weight-j`: J-type instructions
- `--weight-special`: Special instructions (ecall, ebreak)

Default weight for all instructions is 1.0. Weights are relative probabilities.

### Load/Store Address Range Control

Control the offset range for load and store instructions (lb, lh, lw, lbu, lhu, sb, sh, sw):

```bash
# Generate load/store instructions with offsets between -100 and 100
python -m generator --load-store-offset-min -100 --load-store-offset-max 100

# Use hexadecimal values for address ranges
python -m generator --load-store-offset-min 0x0 --load-store-offset-max 0xfff

# Generate load-store pattern with restricted offset range
python -m generator --pattern load-store --load-store-offset-min -50 --load-store-offset-max 50

# Combine with other options
python -m generator --pattern mixed --load-store-offset-min -500 --load-store-offset-max 500 -f asm
```

Arguments:
- `--load-store-offset-min`: Minimum offset for load/store instructions (default: -2048)
- `--load-store-offset-max`: Maximum offset for load/store instructions (default: 2047)

Note: Offsets are 12-bit signed immediates in RISC-V. Values outside the range -2048..2047 will be truncated when encoded. Other instruction types (addi, xori, etc.) use their own default immediate ranges.

### Configuration Files

You can use a YAML configuration file to manage command-line arguments. Command-line arguments override settings from the configuration file.

Create a configuration file (e.g., `config.yaml`):

```yaml
# config.yaml - Example configuration
count: 100
format: "hexasm"
seed: 42
output: "instructions.txt"
pc_comments: true
base_address: 0x1000
list_instructions: false
by_format: null
pattern: "mixed"
pattern_density: 0.3
load_store_offset_min: -100
load_store_offset_max: 100

# Weights as nested dictionary (maps to --weight-* args)
weights:
  r: 2.0
  i: 0.5
  s: 1.0
  b: 1.5
  u: 1.0
  j: 1.0
  special: 0.0
```

Use the configuration file with the `--config` argument:

```bash
# Load configuration and generate instructions
python -m generator --config config.yaml

# Override specific settings from command line
python -m generator --config config.yaml --count 50 --pattern random

# Combine with other CLI arguments (CLI overrides config)
python -m generator --config config.yaml --weight-r 3.0 --output custom.txt
```

**Precedence**: Command-line arguments always override configuration file settings.

**Note**: Configuration file support requires PyYAML (installed automatically with the package).

### List available instructions

Show all supported instructions:

```bash
python -m generator --list-instructions
```

### Save to file

```bash
python -m generator -n 100 -o instructions.txt
```

## Examples

```bash
# Generate 5 random branch instructions
python -m generator -n 5 --by-format B

# Generate store instructions in binary format
python -m generator --by-format S -f bin

# Generate mixed instructions with seed for reproducibility
python -m generator -n 20 -s 12345 -f all -o output.txt

# Weighted generation: more R-type, fewer I-type instructions
python -m generator -n 50 --weight-r 2.5 --weight-i 0.8

# Eliminate special instructions (ecall, ebreak)
python -m generator -n 100 --weight-special 0.0

# Generate instructions with hex as comment (hexasm format)
python -m generator -n 10 -f hexasm

# Generate hexasm with hex as field (old behavior)
python -m generator -n 5 -f hexasm --no-hex-comments

# Generate assembly with PC comments starting at 0x1000
python -m generator -n 10 --pc-comments --base-address 0x1000 -f asm

# Load/store instructions with restricted offset range
python -m generator --pattern load-store --load-store-offset-min -100 --load-store-offset-max 100 -f asm

# Generate instructions using configuration file
python -m generator --config config.yaml
```

## Project Structure

- `riscv_isa.py`: Core classes for RISC-V instruction formats and encoding
- `generator.py`: Command-line interface and main generator logic
- `__main__.py`: Module entry point
- `setup.py`: Package installation configuration
- `tests/`: Unit tests (to be added)

## Supported Instructions

Currently supports RV32I base instruction set:

- **R-type**: add, sub, xor, or, and, sll, srl, sra, slt, sltu
- **I-type**: addi, xori, ori, andi, slli, srli, srai, slti, sltiu, lb, lh, lw, lbu, lhu, jalr
- **S-type**: sb, sh, sw
- **B-type**: beq, bne, blt, bge, bltu, bgeu
- **U-type**: lui, auipc
- **J-type**: jal
- **Special**: ecall, ebreak

## Limitations

- Currently only supports RV32I (32-bit base integer ISA)
- No support for compressed instructions (RV32C)
- No support for multiplication/division extension (M)
- No support for floating-point extensions (F/D)
- Simple random immediate generation (may produce unrealistic values)

## Future Extensions

- Support for RV64I, RV32C, RV32M extensions
- More sophisticated immediate generation (e.g., aligned addresses)
- Weighted instruction distribution
- Basic block generation
- Integration with Spike or other RISC-V simulators

## Claude Code Integration

This project includes Claude Code integration with skill scripts for common operations:

### Available Skills
- **Test Runner**: Run unit tests with `./.claude/skills/skill-test.sh`
- **Instruction Generator**: Generate instructions with `./.claude/skills/skill-generate.sh`
- **Instruction Lister**: List available instructions with `./.claude/skills/skill-list.sh`
- **Configuration Validator**: Validate config files with `./.claude/skills/skill-validate.sh`
- **Register Range Tester**: Test register range control with `./.claude/skills/skill-regtest.sh`

See [CLAUDE.md](CLAUDE.md) for detailed skill documentation and usage examples.

## License

MIT
