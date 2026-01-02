# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **riscv_rtg** - a RISC-V ISA Random Instruction Generator written in Python. It generates random RISC-V RV32I and RV32M instructions for testing simulators, processors, and educational purposes.

## Architecture

The project follows a modular architecture with clear separation of concerns:

### Core Components

1. **`isa/` module** - Foundation layer
   - `Instruction` base class for all RISC-V instructions
   - `RISCVISA` class manages instruction set and random generation
   - `InstructionFormat` enum (R, I, S, B, U, J) matching C++ `RiscvInstructionType`
   - `Registers` enum (x0-x31)
   - Unified YAML instruction definitions in `isa/definitions/`
   - Handles instruction encoding/decoding for all formats

2. **`generator/cli.py`** - Application layer
   - CLI interface with argparse
   - Configuration file loading (YAML via PyYAML)
   - Output formatting (hex, bin, asm, hexasm, all)
   - Weighted random generation control
   - PC comment generation

3. **`generator/patterns.py`** - Advanced features layer
   - `SemanticState` class tracks register/memory state
   - `PatternGenerator` class generates instruction patterns
   - `CommentGenerator` class adds semantic comments
   - Supports data hazards (RAW, WAR, WAW), control flow, memory patterns

4. **`__main__.py`** - Entry point wrapper to `generator.main()`

5. **`scripts/generate_cpp.py`** - C++ code generation layer
   - Generates C++ headers and source files from YAML definitions
   - Creates `riscv_isa_generated.h` and `riscv_isa_generated.cpp`
   - Ensures consistency between Python generator and shader system
   - Enables integration with the shader system's `riscv_isa.h`

### Component Relationships
```
Unified YAML Definitions (isa/definitions/rv32i.yaml)
        ↗                               ↖
       ↗                                 ↖
      ↗                                   ↖
     ↗                                     ↖
    ↗                                       ↖
   ↗                                         ↖
  ↗                                           ↖
 ↗                                             ↖
↗                                               ↖
RISCVISA (Python)                          generate_cpp.py (C++ generator)
    ↓                                           ↓
Instruction objects                       C++ headers/source
    ↓                                           ↓
CLI (generator/cli.py)                     Shader System
    ↓
PatternGenerator (generator/patterns.py)
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

### C++ Code Generation
```bash
# Generate C++ headers and source from YAML definitions
python3 scripts/generate_cpp.py

# Generated files:
# - generated/riscv_isa_generated.h: Instruction metadata and lookup tables
# - generated/riscv_isa_generated.cpp: Static data definitions
# - generated/test_consistency.py: Python verification test

# Test shader system integration
python3 generated/test_shader_integration.py
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

The project includes bash skill scripts for common operations in `.claude/skills/`. These can be invoked directly or referenced in Claude Code interactions. Note: The constraint system has moved to `src/riscv_rtg/constraints/`.

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

**6. RV32M Instruction Tester** (`skill-test-rv32m.sh`):
```bash
./.claude/skills/skill-test-rv32m.sh               # Test RV32M generation (10000 instructions)
./.claude/skills/skill-test-rv32m.sh --count 5000  # Custom instruction count
./.claude/skills/skill-test-rv32m.sh --verbose     # Detailed output
```

**7. C++ Code Generator** (`skill-generate-cpp.sh`):
```bash
./.claude/skills/skill-generate-cpp.sh             # Generate C++ headers/source
./.claude/skills/skill-generate-cpp.sh --clean     # Clean and regenerate
./.claude/skills/skill-generate-cpp.sh --copy      # Copy to shader system
./.claude/skills/skill-generate-cpp.sh --test      # Run integration test
```

**8. Shader System Integration Tester** (`skill-integration-test.sh`):
```bash
./.claude/skills/skill-integration-test.sh         # Run integration test
./.claude/skills/skill-integration-test.sh --generate # Generate files first
./.claude/skills/skill-integration-test.sh --copy  # Copy headers then test
./.claude/skills/skill-integration-test.sh --build # Build shader system tests
```

**9. Instruction Encoding Tester** (`skill-encode.sh`):
```bash
./.claude/skills/skill-encode.sh                   # Test encoding/decoding (100 instructions)
./.claude/skills/skill-encode.sh -n 50 -s 456      # Custom count and seed
./.claude/skills/skill-encode.sh --all-formats     # Test all instruction formats
./.claude/skills/skill-encode.sh --specific r      # Test specific format (R-type)
./.claude/skills/skill-encode.sh --verbose         # Detailed output
```

**10. Consistency Checker** (`skill-consistency.sh`):
```bash
./.claude/skills/skill-consistency.sh --check-all  # Check all consistency aspects
./.claude/skills/skill-consistency.sh --generate --check-all # Generate C++ files first
./.claude/skills/skill-consistency.sh --check-yaml --verbose # Check YAML consistency
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

The pattern system in `generator/patterns.py` enables sophisticated instruction sequences:

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
1. Add to `InstructionFormat` enum in `isa/riscv_isa.py`
2. Update `Instruction` class encoding/decoding methods
3. Add instruction definitions in `RISCVISA.__init__()`
4. Update tests in `tests/test_riscv_isa.py`

### To add a new pattern:
1. Add pattern method to `PatternGenerator` class in `generator/patterns.py`
2. Update pattern selection logic in `generator/cli.py`
3. Add CLI argument handling if needed
4. Update configuration file parsing

### To add a new output format:
1. Add format constant in `generator/cli.py`
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
- **API**: Import `RISCVISA` from `riscv_rtg.isa.riscv_isa` for programmatic use
- **Examples**: See `examples/basic_usage.py` for API usage

## File Organization Principles

1. **Separation of Concerns**: Encoding logic separate from CLI and patterns
2. **Extensibility**: Easy to add new instructions, formats, or patterns
3. **Configuration Driven**: YAML configs for complex scenarios
4. **Test Coverage**: Unit tests for each component
5. **Documentation**: Comprehensive README with examples

## Implementation Status ✅

The project has successfully completed a major refactoring to unify instruction definitions, integrate with the shader system, and add RV32M multiply/divide extension. The following tasks have been completed:

### Initial Verification Tests ✅ (Completed)

1. **✅ Run test suite** to verify the YAML-based instruction loading works correctly:
   ```bash
   python -m pytest tests/
   ```
   Or using the skill:
   ```bash
   ./.claude/skills/skill-test.sh
   ```

2. **✅ Test basic instruction generation** to ensure the CLI still works:
   ```bash
   python -m generator -n 5 -f asm
   ```

### Completed Implementation Tasks ✅

3. **✅ Phase 4: C++ Code Generation** (Completed)
   - ✅ Created/verified `scripts/generate_cpp.py` script
   - ✅ Generated C++ headers (`generated/riscv_isa_generated.h`)
   - ✅ Generated C++ source (`generated/riscv_isa_generated.cpp`)
   - ✅ Ran the generation script:
     ```bash
     python3 scripts/generate_cpp.py
     ```

4. **✅ Phase 5: Shader System Integration** (Completed)
   - ✅ Copied generated headers to shader system include directory
   - ✅ Updated shader system's `riscv_isa.h` to include generated headers
   - ✅ Tested integration using existing shader system test:
     ```bash
     cd ../shader_system && make test_riscv_decode
     ```
   - ✅ Updated shader system Makefile to include generated sources
   - ✅ Verified simulator builds successfully with generated files

5. **✅ Phase 6: Comprehensive Testing** (Completed)
   - ✅ Ran integration test: `python3 generated/test_shader_integration.py`
   - ✅ Validated instruction consistency between Python and C++
   - ✅ Tested pattern generation with new structure
   - ✅ Ran existing test suite (37 tests passed)
   - ✅ Verified edge cases and instruction decoding

6. **✅ Phase 7: RV32M Extension** (Completed)
   - ✅ Added RV32M (multiply/divide) instructions to YAML definitions
   - ✅ Updated Python enums (`enums.py`) with MULDIV funct7 and RV32M funct3 values
   - ✅ Updated C++ header (`riscv_isa.h`) with RV32M enum values
   - ✅ Regenerated C++ files (`scripts/generate_cpp.py`)
   - ✅ Verified RV32M instruction generation and encoding
   - ✅ Test suite passes with 47 total instructions (was 37)

7. **✅ Phase 8: Documentation Updates** (Completed)
   - ✅ Updated examples to demonstrate shader system integration
   - ✅ Added tutorial for using generated instructions in C++ tests ([examples/cpp_test_tutorial.md](examples/cpp_test_tutorial.md))
   - ✅ Documented YAML definition format for adding new instructions ([examples/yaml_definition_format.md](examples/yaml_definition_format.md))
   - ✅ Updated README.md with RV32M support and documentation links
   - ✅ Updated CLAUDE.md with completion status

### Future Enhancements

6. **Extend ISA Support** (RV32M completed ✅)
   - ✅ RV32M (multiply/divide) instructions added to YAML definitions
   - Add RV32C (compressed) instructions
   - Support custom GPU extensions via CUSTOM opcode

7. **Improve Testing**
   - Add more integration tests with shader system
   - Create comparative decoding tests (Python vs C++)
   - Add performance benchmarks for instruction generation

8. **Documentation Updates** (Completed ✅)
   - ✅ Updated examples to demonstrate shader system integration
   - ✅ Added tutorial for using generated instructions in C++ tests
   - ✅ Documented YAML definition format for adding new instructions
   - See [examples/cpp_test_tutorial.md](examples/cpp_test_tutorial.md) and [examples/yaml_definition_format.md](examples/yaml_definition_format.md)

### Critical Verification Points ✅ (Verified)

- ✅ Verify opcode values match exactly between YAML and C++ header
- ✅ Ensure immediate value generation follows RISC-V specification
- ✅ Test edge cases for all instruction formats (R, I, S, B, U, J)
- ✅ Confirm backward compatibility for existing CLI users

*All critical verification points have been successfully validated during Phase 6 comprehensive testing.*

Use the skills in `.claude/skills/` for common development tasks, and refer to the comprehensive plan at `/home/kawaii/.claude/plans/twinkly-bubbling-quiche.md` for detailed implementation steps.