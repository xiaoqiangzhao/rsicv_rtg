# Claude Code Skills for riscv_rtg

This directory contains skill scripts for common operations in the RISC-V Random Instruction Generator project.

## Available Skills

### 1. `skill-test.sh` - Run tests
```bash
./.claude/skills/skill-test.sh
# or with pytest options
./.claude/skills/skill-test.sh -v
```

### 2. `skill-generate.sh` - Generate instructions
```bash
# Basic generation
./.claude/skills/skill-generate.sh

# With options
./.claude/skills/skill-generate.sh -n 20 -f hexasm -p load-store

# Test register ranges
./.claude/skills/skill-generate.sh --regtest
```

### 3. `skill-list.sh` - List available instructions
```bash
# Simple list
./.claude/skills/skill-list.sh

# Detailed list
./.claude/skills/skill-list.sh --detailed
```

### 4. `skill-validate.sh` - Validate configuration file
```bash
# Validate default config
./.claude/skills/skill-validate.sh

# Validate specific config
./.claude/skills/skill-validate.sh my_config.yaml
```

### 5. `skill-regtest.sh` - Test register range control
```bash
# Test with default ranges (rd=5-7, rs1=6-6, rs2=7-7)
./.claude/skills/skill-regtest.sh

# Test custom ranges
./.claude/skills/skill-regtest.sh --rd-min 10 --rd-max 15

# Test all registers
./.claude/skills/skill-regtest.sh --all
```

### 6. `skill-test-rv32m.sh` - Test RV32M multiply/divide instruction generation
```bash
# Basic test (10000 instructions, seed 42)
./.claude/skills/skill-test-rv32m.sh

# With custom count and seed
./.claude/skills/skill-test-rv32m.sh --count 5000 --seed 123

# Verbose output
./.claude/skills/skill-test-rv32m.sh --verbose
```

### 7. `skill-generate-cpp.sh` - Generate C++ headers and source from YAML definitions
```bash
# Basic generation
./.claude/skills/skill-generate-cpp.sh

# Clean and regenerate
./.claude/skills/skill-generate-cpp.sh --clean

# Generate and copy to shader system
./.claude/skills/skill-generate-cpp.sh --copy

# Generate and run integration test
./.claude/skills/skill-generate-cpp.sh --test
```

### 8. `skill-integration-test.sh` - Test shader system integration
```bash
# Basic integration test
./.claude/skills/skill-integration-test.sh

# Generate files first, then test
./.claude/skills/skill-integration-test.sh --generate

# Copy to shader system and test
./.claude/skills/skill-integration-test.sh --copy

# Build shader system tests after copying
./.claude/skills/skill-integration-test.sh --build
```

### 9. `skill-encode.sh` - Test instruction encoding/decoding
```bash
# Basic encoding test (100 instructions)
./.claude/skills/skill-encode.sh

# Test specific count and seed
./.claude/skills/skill-encode.sh -n 50 -s 456

# Test all instruction formats
./.claude/skills/skill-encode.sh --all-formats

# Test specific format (R-type)
./.claude/skills/skill-encode.sh --specific r

# Verbose output
./.claude/skills/skill-encode.sh --verbose
```

### 10. `skill-consistency.sh` - Check consistency between Python and C++ definitions
```bash
# Check all consistency aspects
./.claude/skills/skill-consistency.sh --check-all

# Generate C++ files first, then check
./.claude/skills/skill-consistency.sh --generate --check-all

# Check YAML definition consistency
./.claude/skills/skill-consistency.sh --check-yaml --verbose

# Default: check-all with verbose
./.claude/skills/skill-consistency.sh --verbose
```

## Integration with Claude Code

These skills can be integrated with Claude Code in several ways:

1. **Direct invocation**: Claude can run these scripts using Bash tool
2. **Skill registration**: Could be registered as Claude Code skills (if supported)
3. **Documentation**: Included in CLAUDE.md for reference

## Adding New Skills

To add a new skill:
1. Create a `skill-<name>.sh` script in this directory
2. Make it executable: `chmod +x skill-<name>.sh`
3. Add documentation to this README
4. Update CLAUDE.md with the new skill

## Skill Design Principles

- **Simple**: One main purpose per skill
- **Documented**: Help text and usage examples
- **Robust**: Error handling and validation
- **Consistent**: Similar argument patterns across skills