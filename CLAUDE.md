# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **riscv_rtg** - a RISC-V ISA Random Instruction Generator written in Python. It generates random RISC-V RV32I instructions for testing simulators, processors, and educational purposes.

## Architecture

The project follows a modular architecture with clear separation of concerns:

### Core Components

1. **`riscv_isa.py`** - Foundation layer
   - `Instruction` base class for all RISC-V instructions
   - `RISCVISA` class manages instruction set and random generation
   - `InstructionFormat` enum (R, I, S, B, U, J)
   - `Registers` enum (x0-x31)
   - Handles instruction encoding/decoding for all formats

2. **`generator.py`** - Application layer
   - CLI interface with argparse
   - Configuration file loading (YAML via PyYAML)
   - Output formatting (hex, bin, asm, hexasm, all)
   - Weighted random generation control
   - PC comment generation

3. **`patterns.py`** - Advanced features layer
   - `SemanticState` class tracks register/memory state
   - `PatternGenerator` class generates instruction patterns
   - `CommentGenerator` class adds semantic comments
   - Supports data hazards (RAW, WAR, WAW), control flow, memory patterns

4. **`__main__.py`** - Entry point wrapper to `generator.main()`

### Component Relationships
```
CLI (generator.py) → RISCVISA (riscv_isa.py) → Instruction objects
                    ↓
              PatternGenerator (patterns.py)
                    ↓
              Output Formatters
```

## Development Commands

### Installation
```bash
# Install as editable package (recommended for development)
pip install -e .

# Use directly without installation
python -m generator --help
```

### Testing
```bash
# Run all tests (uses unittest/pytest)
python -m pytest tests/

# Alternative test runner
python -m unittest discover tests

# Run specific test file
python -m pytest tests/test_riscv_isa.py
```

### Common Development Tasks

**Generate test instructions:**
```bash
# Basic generation (10 instructions, hex format)
python -m generator

# Assembly format with PC comments
python -m generator -n 20 -f asm --pc-comments --base-address 0x1000

# Pattern-based generation
python -m generator --pattern mixed --pattern-density 0.3 -f hexasm

# With configuration file
python -m generator --config example_config.yaml
```

**List available instructions:**
```bash
python -m generator --list-instructions
```

**Test specific features:**
```bash
# Test load/store offset ranges
python -m generator --load-store-offset-min -100 --load-store-offset-max 100 -f asm

# Test weighted generation
python -m generator --weight-r 2.0 --weight-i 0.5 --weight-special 0.0

# Test semantic patterns
python -m generator --pattern raw --semantic-correlation --semantic-comments
```

## Skills

The project includes bash skill scripts for common operations in `.claude/skills/`. These can be invoked directly or referenced in Claude Code interactions.

### Available Skills

**1. Test Runner** (`skill-test.sh`):
```bash
./.claude/skills/skill-test.sh           # Run all tests
./.claude/skills/skill-test.sh -v        # Verbose output
```

**2. Instruction Generator** (`skill-generate.sh`):
```bash
./.claude/skills/skill-generate.sh                    # Generate 10 asm instructions
./.claude/skills/skill-generate.sh -n 20 -f hexasm    # 20 instructions in hexasm
./.claude/skills/skill-generate.sh -p load-store      # Load-store pattern
./.claude/skills/skill-generate.sh --regtest          # Test register ranges
```

**3. Instruction Lister** (`skill-list.sh`):
```bash
./.claude/skills/skill-list.sh           # List instruction names
./.claude/skills/skill-list.sh --detailed # Detailed list with formats
```

**4. Configuration Validator** (`skill-validate.sh`):
```bash
./.claude/skills/skill-validate.sh                  # Validate example_config.yaml
./.claude/skills/skill-validate.sh my_config.yaml   # Validate custom config
```

**5. Register Range Tester** (`skill-regtest.sh`):
```bash
./.claude/skills/skill-regtest.sh                  # Test default ranges
./.claude/skills/skill-regtest.sh --all            # Test all registers 0-31
./.claude/skills/skill-regtest.sh --rd-min 10 --rd-max 15  # Custom ranges
```

### Skill Integration

Claude Code can use these skills in several ways:
1. **Direct execution**: Use Bash tool to run skill scripts
2. **Skill references**: Mention skills in conversation context
3. **Task automation**: Chain skills together for complex workflows

### Skill Development

To create a new skill:
1. Add script to `.claude/skills/skill-<name>.sh`
2. Make executable: `chmod +x skill-<name>.sh`
3. Document in `.claude/skills/README.md`
4. Update this CLAUDE.md file

## Configuration System

- **CLI arguments** always override configuration file settings
- **YAML configuration** files provide preset command sets (see `example_config.yaml`)
- **Precedence**: CLI args > YAML config > defaults

Key configuration options:
- `pattern`: random, load-store, raw, war, waw, basic-block, mixed
- `weights`: Relative probabilities for instruction types (r, i, s, b, u, j, special)
- `load_store_ranges`: Multiple offset ranges as "base:size" pairs
- `semantic_correlation`: Enable data/control/memory/function correlations
- `semantic_comments`: Add semantic annotations to output

## Output Formats

- `hex`: Hexadecimal (e.g., `0x12345678`)
- `bin`: 32-bit binary
- `asm`: Assembly syntax (e.g., `add x1, x2, x3`)
- `hexasm`: Assembly with hex comment (or hex as field with `--no-hex-comments`)
- `all`: All formats combined

## Pattern Generation System

The pattern system in `patterns.py` enables sophisticated instruction sequences:

### Pattern Types
- `load-store`: Memory access patterns with address ranges
- `raw`: Read-after-write data hazards
- `war`: Write-after-read data hazards
- `waw`: Write-after-write data hazards
- `basic-block`: Control flow with branches
- `mixed`: Combination of patterns with configurable density

### Semantic State Tracking
- Register usage (writers/readers)
- Memory access patterns by base register
- Control flow (loops, branches)
- Function context (stack pointer, saved registers)

## Adding New Features

### To add a new instruction format:
1. Add to `InstructionFormat` enum in `riscv_isa.py`
2. Update `Instruction` class encoding/decoding methods
3. Add instruction definitions in `RISCVISA.__init__()`
4. Update tests in `tests/test_riscv_isa.py`

### To add a new pattern:
1. Add pattern method to `PatternGenerator` class in `patterns.py`
2. Update pattern selection logic in `generator.py`
3. Add CLI argument handling if needed
4. Update configuration file parsing

### To add a new output format:
1. Add format constant in `generator.py`
2. Implement formatting function
3. Update `format_instruction()` function
4. Update CLI argument validation

## Testing Strategy

- **Unit tests** in `tests/` directory cover core functionality
- **Test files**:
  - `test_riscv_isa.py`: Core instruction encoding/decoding
  - `test_config.py`: Configuration file parsing
  - `test_semantic.py`: Pattern generation and semantic tracking
- **Test command**: `python -m pytest tests/`

## Key Design Patterns

1. **Command Pattern**: CLI arguments map to generator parameters
2. **Strategy Pattern**: Different output formatters for different formats
3. **State Pattern**: `SemanticState` tracks execution context
4. **Factory Pattern**: `RISCVISA` creates instruction objects
5. **Builder Pattern**: `PatternGenerator` constructs instruction sequences

## Dependencies

- **Core**: Python 3.6+, PyYAML>=6.0
- **Testing**: pytest>=6.0 (optional)
- **No build process**: Pure Python package

## Entry Points

- **CLI**: `riscv-rtg` (after installation) or `python -m generator`
- **API**: Import `RISCVISA` from `riscv_isa` for programmatic use
- **Examples**: See `examples/basic_usage.py` for API usage

## File Organization Principles

1. **Separation of Concerns**: Encoding logic separate from CLI and patterns
2. **Extensibility**: Easy to add new instructions, formats, or patterns
3. **Configuration Driven**: YAML configs for complex scenarios
4. **Test Coverage**: Unit tests for each component
5. **Documentation**: Comprehensive README with examples