# ISA Constraint Configuration

This directory contains YAML templates and examples for defining instruction constraints for the RISC-V Random Instruction Generator (riscv_rtg).

## Purpose

The constraint system allows fine-grained control over instruction generation by specifying:
- Allowed registers for rd, rs1, rs2
- Immediate value ranges for different instruction types
- Zero register restrictions
- Relative probability weights for instruction selection
- Grouping of instructions for constraint application

## Files

### `constraint_template.yaml`
A comprehensive template showing all available constraint options with detailed comments. Use this as a reference when creating custom constraint configurations.

### `example_constraint.yaml`
A practical example showing constraints for common testing scenarios:
- Arithmetic operations on temporary registers
- Stack-relative memory operations
- Function call patterns
- Control flow with small branches

## Constraint Structure

### Global Constraints
Apply to all instructions unless overridden:

```yaml
global_constraints:
  registers:
    rd_allowed: [0, 1, 2, ...]  # List of allowed register numbers
    rs1_allowed: [0, 1, 2, ...]
    rs2_allowed: [0, 1, 2, ...]
    exclude_zero_rd: false      # Whether x0 is allowed for rd
    exclude_zero_rs1: false     # Whether x0 is allowed for rs1
    exclude_zero_rs2: false     # Whether x0 is allowed for rs2

    # Alternative to allowed lists:
    rd_range:
      min: 0
      max: 31
    rs1_range:
      min: 0
      max: 31
    rs2_range:
      min: 0
      max: 31

  immediates:
    i_type:     # I-type (addi, loads, etc.)
      min: -2048
      max: 2047
    s_type:     # S-type (stores)
      min: -2048
      max: 2047
    b_type:     # B-type (branches) - in bytes, must be multiple of 2
      min: -4096
      max: 4094
      alignment: 2
    u_type:     # U-type (lui, auipc)
      min: 0
      max: 0xFFFFF
    j_type:     # J-type (jal) - in bytes, must be multiple of 2
      min: -1048576
      max: 1048574
      alignment: 2

  weight: 1.0  # Relative probability
```

### Instruction Groups
Group instructions to apply common constraints:

```yaml
instruction_groups:
  group_name:
    description: "Human-readable description"
    instructions: ["add", "sub", "xor"]  # List of instruction names
    constraints:
      # Same structure as global_constraints
      registers: ...
      immediates: ...
      weight: ...
```

### Instruction Overrides
Highest precedence - override group constraints for specific instructions:

```yaml
instruction_overrides:
  addi:
    description: "Specific constraints for addi"
    constraints:
      # Same structure as global_constraints
```

## Constraint Precedence

Constraints are applied in this order (later overrides earlier):
1. `global_constraints` - Base constraints for all instructions
2. `instruction_groups` - Applied in order of definition
3. `instruction_overrides` - Instruction-specific constraints

Within each level:
- Lists (`rd_allowed`, etc.) are replaced entirely
- Boolean flags (`exclude_zero_rd`, etc.) are replaced
- Ranges (`min`/`max`) are replaced
- Weights are multiplied (global × group × override)

## Register Conventions

Common RISC-V register usage:

| Register | Number | Name    | Conventional Use                    |
|----------|--------|---------|-------------------------------------|
| x0       | 0      | zero    | Hard-wired zero                     |
| x1       | 1      | ra      | Return address                      |
| x2       | 2      | sp      | Stack pointer                       |
| x3       | 3      | gp      | Global pointer                      |
| x4       | 4      | tp      | Thread pointer                      |
| x5-x7    | 5-7    | t0-t2   | Temporary registers                 |
| x8-x9    | 8-9    | s0-s1   | Saved registers / frame pointer     |
| x10-x17  | 10-17  | a0-a7   | Argument registers                  |
| x18-x27  | 18-27  | s2-s11  | Saved registers                     |
| x28-x31  | 28-31  | t3-t6   | Temporary registers                 |

## Immediate Ranges

Standard RISC-V immediate ranges:
- **I-type/S-type**: 12-bit signed (-2048 to 2047)
- **B-type**: 13-bit signed, 2-byte aligned (-4096 to 4094)
- **U-type**: 20-bit unsigned (0 to 0xFFFFF)
- **J-type**: 21-bit signed, 2-byte aligned (-1048576 to 1048574)

## Usage with riscv_rtg

To use constraint configurations with riscv_rtg, the generator would need to be extended to:
1. Load and parse constraint YAML files
2. Apply constraints during instruction generation
3. Respect register and immediate restrictions
4. Use weights for probability-based selection

### Example Integration

```python
# Pseudocode for constraint integration
from constraint_loader import load_constraints

constraints = load_constraints("isa_constraint/example_constraint.yaml")

# During instruction generation:
def generate_constrained_instruction(isa, constraints, instr_name):
    instr = isa.get_instruction_by_name(instr_name)

    # Apply register constraints
    if instr_name in constraints:
        reg_constraints = constraints[instr_name].get("registers", {})
        rd = select_register(reg_constraints.get("rd_allowed"))
        rs1 = select_register(reg_constraints.get("rs1_allowed"))
        rs2 = select_register(reg_constraints.get("rs2_allowed"))

    # Apply immediate constraints
    imm_constraints = constraints[instr_name].get("immediates", {})
    imm = generate_immediate(imm_constraints.get(instr.format))

    return instr.encode(rd=rd, rs1=rs1, rs2=rs2, imm=imm)
```

## Future Extensions

Potential enhancements to the constraint system:
1. **Dependency constraints**: Specify register dependencies between instructions
2. **Sequence patterns**: Define multi-instruction patterns with constraints
3. **Memory access patterns**: Constraints on address alignment and access size
4. **Control flow constraints**: Valid branch targets and jump ranges
5. **Timing constraints**: Pipeline hazards and timing requirements

## See Also

- [riscv_rtg README](../README.md) - Main project documentation
- [CLAUDE.md](../CLAUDE.md) - Claude Code integration guide
- [example_config.yaml](../example_config.yaml) - General configuration example