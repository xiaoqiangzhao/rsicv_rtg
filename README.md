# RISC-V ISA Random Instruction Generator (riscv_rtg)

A Python 3 tool for generating random RISC-V instructions. Useful for testing RISC-V simulators, processors, and educational purposes.

## Features

- Generates random RISC-V RV32I instructions
- Supports all instruction formats: R, I, S, B, U, J
- Output in multiple formats: hexadecimal, binary, assembly, or all
- Filter by instruction format
- Reproducible generation with seed support
- Lists all available instructions

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/riscv_rtg.git
cd riscv_rtg
```

Install as a package:

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
- `all`: All of the above

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

## License

MIT
