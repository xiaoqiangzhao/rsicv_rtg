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