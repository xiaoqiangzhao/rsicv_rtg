# YAML Instruction Definition Format

This document describes the YAML format used to define RISC-V instructions in `riscv_rtg`. The YAML file serves as a single source of truth for both Python instruction generation and C++ shader system decoding.

## File Location

Instruction definitions are stored in:
```
src/riscv_rtg/isa/definitions/rv32i.yaml
```

## Overview

The YAML file has two main sections:
1. **Enums**: Opcode, funct3, and funct7 values matching C++ `riscv_isa.h`
2. **Instructions**: Individual instruction definitions mapping enums to mnemonics

## Enum Definitions

### Opcode Enum (`enums.opcode`)

Defines RISC-V instruction opcodes. Each entry maps an enum name to its 7-bit binary value.

```yaml
enums:
  opcode:
    LOAD: 0b0000011    # 3
    STORE: 0b0100011   # 35
    OP_IMM: 0b0010011  # 19
    OP: 0b0110011      # 51
    # ... etc
```

**Important**: These values must match exactly the C++ `RiscvOpcode` enum in `riscv_isa.h`.

### Funct3 Enum (`enums.funct3`)

Defines function code 3 values. Organized by instruction category:

```yaml
enums:
  funct3:
    # Load
    LB: 0b000
    LH: 0b001
    LW: 0b010
    LBU: 0b100
    LHU: 0b101

    # Store
    SB: 0b000
    SH: 0b001
    SW: 0b010

    # OP-IMM
    ADDI: 0b000
    SLTI: 0b010
    SLTIU: 0b011
    XORI: 0b100
    ORI: 0b110
    ANDI: 0b111
    SLLI: 0b001
    SRLI_SRAI: 0b101

    # OP
    ADD_SUB: 0b000
    SLL: 0b001
    SLT: 0b010
    SLTU: 0b011
    XOR: 0b100
    SRL_SRA: 0b101
    OR: 0b110
    AND: 0b111

    # Multiply/Divide extension (same funct3 values, different funct7)
    MUL: 0b000
    MULH: 0b001
    MULHSU: 0b010
    MULHU: 0b011
    DIV: 0b100
    DIVU: 0b101
    REM: 0b110
    REMU: 0b111

    # ... etc
```

**Note**: Some funct3 values are reused across different opcodes (e.g., `0b000` for `LB`, `SB`, `ADDI`, `BEQ`). The context is determined by the opcode.

### Funct7 Enum (`enums.funct7`)

Defines function code 7 values (used in R-type instructions):

```yaml
enums:
  funct7:
    BASE: 0b0000000    # For most instructions
    ALT: 0b0100000     # For SRAI, SUB, SRA
    MULDIV: 0b0000001  # For multiply/divide extension
```

## Instruction Definitions

Each instruction is defined as an entry in the `instructions` list.

### Basic Structure

```yaml
instructions:
  - mnemonic: add        # Instruction name (lowercase)
    format: R_TYPE       # Instruction format
    opcode: OP           # Reference to opcode enum
    funct3: ADD_SUB      # Reference to funct3 enum (optional)
    funct7: BASE         # Reference to funct7 enum (optional)
    immediate: null      # Immediate specification (null if none)
```

### Instruction Formats

Supported formats (must match `RiscvInstructionType` in C++):
- `R_TYPE`: Register-register (e.g., `add x1, x2, x3`)
- `I_TYPE`: Immediate (e.g., `addi x1, x2, 100`)
- `S_TYPE`: Store (e.g., `sw x1, 100(x2)`)
- `B_TYPE`: Branch (e.g., `beq x1, x2, label`)
- `U_TYPE`: Upper immediate (e.g., `lui x1, 0x10000`)
- `J_TYPE`: Jump (e.g., `jal x1, label`)

### Immediate Specifications

For instructions with immediates, define the immediate field:

```yaml
immediate:
  bits: 12           # Bit width of immediate field
  signed: true       # Whether immediate is signed
  range: [-2048, 2047]  # Generation range (inclusive)
  align: 1           # Alignment requirement (1=no alignment)
```

#### Format-Specific Immediate Details

**I-type instructions** (e.g., `addi`, loads):
```yaml
immediate:
  bits: 12
  signed: true
  range: [-2048, 2047]
```

**Load instructions** (`lb`, `lh`, `lw`, `lbu`, `lhu`, `jalr`):
- Use `signed: false` for unsigned loads (`lbu`, `lhu`)
- Range typically matches 12-bit signed/unsigned range

**Shift instructions** (`slli`, `srli`, `srai`):
```yaml
immediate:
  bits: 5           # Only lower 5 bits used (shamt)
  signed: false
  range: [0, 31]
```

**S-type instructions** (stores):
```yaml
immediate:
  bits: 12
  signed: true
  range: [-2048, 2047]
```

**B-type instructions** (branches):
```yaml
immediate:
  bits: 13          # 13-bit signed, 2-byte aligned
  signed: true
  align: 2          # Must be multiple of 2
  range: [-4096, 4094]
```

**U-type instructions** (`lui`, `auipc`):
```yaml
immediate:
  bits: 20
  signed: false
  range: [0, 1048575]  # 0x00000 to 0xFFFFF
```

**J-type instructions** (`jal`):
```yaml
immediate:
  bits: 21          # 21-bit signed, 2-byte aligned
  signed: true
  align: 2
  range: [-1048576, 1048574]
```

### Special Instructions

**Instructions without immediates** (most R-type):
```yaml
immediate: null
```

**System instructions** (`ecall`, `ebreak`):
```yaml
- mnemonic: ecall
  format: I_TYPE
  opcode: SYSTEM
  funct3: ECALL_EBREAK
  immediate: null

- mnemonic: ebreak
  format: I_TYPE
  opcode: SYSTEM
  funct3: ECALL_EBREAK
  funct7: ALT  # Note: ebreak uses different encoding in some specs
  immediate: null
```

## Adding New Instructions

### Step-by-Step Guide

#### 1. Determine Instruction Properties

For a new instruction, identify:
- **Mnemonic**: Instruction name (e.g., `mul`, `divu`)
- **Format**: R, I, S, B, U, or J-type
- **Opcode**: 7-bit opcode value
- **Funct3**: 3-bit function code (if applicable)
- **Funct7**: 7-bit function code (if R-type)
- **Immediate**: Bit width, signedness, range, alignment

#### 2. Add Enum Values (if needed)

If the instruction uses new opcode, funct3, or funct7 values, add them to the appropriate enum section:

```yaml
# Example: Adding RV32M multiply/divide extension
enums:
  funct7:
    # Add new funct7 value
    MULDIV: 0b0000001

  funct3:
    # Add new funct3 values (same numeric values as existing ones,
    # but named differently for clarity)
    MUL: 0b000
    MULH: 0b001
    MULHSU: 0b010
    MULHU: 0b011
    DIV: 0b100
    DIVU: 0b101
    REM: 0b110
    REMU: 0b111
```

#### 3. Add Instruction Definition

Add the instruction to the `instructions` list in the appropriate category:

```yaml
# Example: Adding RV32M mul instruction
instructions:
  # ... existing instructions ...

  # Multiply/Divide extension (R-type)
  - mnemonic: mul
    format: R_TYPE
    opcode: OP           # Same opcode as other R-type
    funct3: MUL          # Reference to new funct3 enum
    funct7: MULDIV       # Reference to new funct7 enum
    immediate: null      # No immediate
```

#### 4. Update C++ Header (if adding new enum values)

If you added new enum values, update the C++ header to match:

```cpp
// In riscv_isa.h
enum class RiscvFunct7 : uint8_t {
    // ... existing values ...
    MULDIV    = 0b0000001  // For multiply/divide extension
};

enum class RiscvFunct3 : uint8_t {
    // ... existing values ...
    // Multiply/Divide extension (same funct3 values, different funct7)
    MUL        = 0b000,
    MULH       = 0b001,
    MULHSU     = 0b010,
    MULHU      = 0b011,
    DIV        = 0b100,
    DIVU       = 0b101,
    REM        = 0b110,
    REMU       = 0b111,
};
```

#### 5. Regenerate C++ Files

Run the generation script to update C++ headers and source files:

```bash
python3 scripts/generate_cpp.py
```

#### 6. Update Python Enums

Update `src/riscv_rtg/isa/enums.py` to match the YAML definitions (this file should be manually kept in sync):

```python
# In enums.py
class RiscvFunct7(IntEnum):
    # ... existing values ...
    MULDIV = 0b0000001

class RiscvFunct3(IntEnum):
    # ... existing values ...
    MUL        = 0b000
    MULH       = 0b001
    # ... etc
```

#### 7. Test the New Instruction

Run tests to verify the new instruction works:

```bash
# Run unit tests
python3 -m unittest discover tests -v

# Generate sample instructions including the new one
python3 -m generator -n 1000 | grep mul

# Run integration test
python3 generated/test_shader_integration.py
```

## Complete Example: Adding RV32C Compressed Instructions

*(Hypothetical example - RV32C not yet implemented)*

```yaml
# 1. Add opcode for compressed extension
enums:
  opcode:
    C0: 0b00          # 2-bit opcode for compressed
    C1: 0b01
    C2: 0b10

  funct3:
    # Compressed funct3 values
    CADDI4SPN: 0b000
    CLW: 0b010
    CSW: 0b110

  funct7:
    # Not typically used in compressed

# 2. Add instruction definitions
instructions:
  # Compressed instructions (would need new format type)
  - mnemonic: c.addi4spn
    format: CI_TYPE     # Would need new format
    opcode: C0
    funct3: CADDI4SPN
    immediate:
      bits: 10
      signed: false
      range: [0, 1023]
      align: 4         # Stack pointer offset must be 4-byte aligned
```

## Validation Rules

### Cross-Language Consistency

The YAML definitions must maintain consistency between:
1. **Python enums** (`enums.py`)
2. **C++ header** (`riscv_isa.h`)
3. **YAML enum values** (`rv32i.yaml`)

### Instruction Encoding Validation

Each instruction definition should satisfy:
1. Opcode value matches RISC-V specification
2. Funct3 value matches specification (if applicable)
3. Funct7 value matches specification (if R-type)
4. Immediate bit width matches instruction format
5. Range fits within bit width

### Generation Validation

When generating instructions:
1. All defined instructions should be generatable
2. Encoded values should match expected bit patterns
3. Assembly output should be parseable

## Common Pitfalls

### 1. Enum Name Conflicts

Different instruction categories may use the same numeric funct3 values. Use distinct enum names:

```yaml
# Correct: Different names for same value
funct3:
  # Load
  LB: 0b000
  # Store
  SB: 0b000  # Same value, different name
  # Branch
  BEQ: 0b000  # Same value, different name
```

### 2. Immediate Range Errors

Ensure immediate ranges fit within the specified bit width:

```yaml
# Correct for 12-bit signed
immediate:
  bits: 12
  signed: true
  range: [-2048, 2047]  # Fits 2^11 range

# Incorrect: exceeds range
immediate:
  bits: 12
  signed: true
  range: [-5000, 5000]  # Too large
```

### 3. Missing Funct7 for R-type

R-type instructions require `funct7` field:

```yaml
# Correct R-type
- mnemonic: add
  format: R_TYPE
  opcode: OP
  funct3: ADD_SUB
  funct7: BASE      # Required
  immediate: null

# Incorrect: missing funct7
- mnemonic: add
  format: R_TYPE
  opcode: OP
  funct3: ADD_SUB   # Missing funct7
  immediate: null
```

### 4. Incorrect Format-Immediate Pairing

Ensure immediate specification matches format:

```yaml
# Correct: I-type with 12-bit immediate
- mnemonic: addi
  format: I_TYPE
  immediate:
    bits: 12
    signed: true

# Incorrect: R-type with immediate
- mnemonic: add
  format: R_TYPE
  immediate:        # R-type should have null
    bits: 12
    signed: true
```

## Testing Changes

### 1. Run Unit Tests

```bash
python3 -m unittest discover tests -v
```

### 2. Generate Sample Instructions

```bash
# Generate instructions including new ones
python3 -m generator -n 1000 --list-instructions

# Check specific instruction appears
python3 -m generator -n 1000 | grep "mul\|div\|rem"
```

### 3. Verify C++ Generation

```bash
# Regenerate and test
python3 scripts/generate_cpp.py
python3 generated/test_consistency.py
python3 generated/test_shader_integration.py
```

### 4. Manual Inspection

Check generated C++ files for new instructions:

```bash
grep -n "mul\|div\|rem" generated/riscv_isa_generated.h
grep -n "mul\|div\|rem" generated/riscv_isa_generated.cpp
```

## Maintenance

### Keeping Enums Synchronized

When modifying YAML definitions:
1. Update `enums.py` to match
2. Update `riscv_isa.h` to match
3. Run `generate_cpp.py` to regenerate
4. Run all tests

### Version Control

Consider the YAML file as the source of truth. Changes should be:
1. Made first in `rv32i.yaml`
2. Propagated to other files
3. Committed with a clear message about instruction additions

## See Also

- [RISC-V Instruction Set Manual](https://riscv.org/technical/specifications/)
- [C++ Test Tutorial](./cpp_test_tutorial.md)
- [Shader System Integration Example](../examples/shader_system_integration.py)
- [Main README](../README.md)