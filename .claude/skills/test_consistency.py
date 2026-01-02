#!/usr/bin/env python3
"""Check consistency between Python and C++ instruction definitions."""

import sys
import os
import yaml

# Add parent directory to path to import riscv_rtg modules
# File is in .claude/skills/, need to go up 3 levels to project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

from riscv_rtg.isa.enums import RiscvOpcode, RiscvFunct3, RiscvFunct7, RiscvInstructionType
from riscv_rtg.isa.riscv_isa import RISCVISA

def check_yaml_consistency(verbose=False):
    """Check YAML definition consistency with Python enums."""
    errors = []

    # Load YAML definitions
    yaml_path = os.path.join(project_root, 'src', 'riscv_rtg', 'isa', 'definitions', 'rv32i.yaml')
    with open(yaml_path, 'r') as f:
        yaml_data = yaml.safe_load(f)

    if verbose:
        print("Checking enum consistency...")

    # Check opcodes
    yaml_opcodes = yaml_data['enums']['opcode']
    python_opcodes = {name: value for name, value in vars(RiscvOpcode).items() if not name.startswith('_')}

    for name, yaml_value in yaml_opcodes.items():
        if name in python_opcodes:
            if python_opcodes[name] != yaml_value:
                errors.append(f'Opcode {name}: YAML={yaml_value}, Python={python_opcodes[name]}')
                if verbose:
                    print(f'❌ Opcode mismatch: {name}')
        else:
            errors.append(f'Opcode {name} in YAML but not in Python')
            if verbose:
                print(f'❌ Missing opcode in Python: {name}')

    # Check funct3
    yaml_funct3 = yaml_data['enums']['funct3']
    python_funct3 = {name: value for name, value in vars(RiscvFunct3).items() if not name.startswith('_')}

    for name, yaml_value in yaml_funct3.items():
        if name in python_funct3:
            if python_funct3[name] != yaml_value:
                errors.append(f'Funct3 {name}: YAML={yaml_value}, Python={python_funct3[name]}')
                if verbose:
                    print(f'❌ Funct3 mismatch: {name}')
        else:
            errors.append(f'Funct3 {name} in YAML but not in Python')
            if verbose:
                print(f'❌ Missing funct3 in Python: {name}')

    # Check funct7
    yaml_funct7 = yaml_data['enums']['funct7']
    python_funct7 = {name: value for name, value in vars(RiscvFunct7).items() if not name.startswith('_')}

    for name, yaml_value in yaml_funct7.items():
        if name in python_funct7:
            if python_funct7[name] != yaml_value:
                errors.append(f'Funct7 {name}: YAML={yaml_value}, Python={python_funct7[name]}')
                if verbose:
                    print(f'❌ Funct7 mismatch: {name}')
        else:
            errors.append(f'Funct7 {name} in YAML but not in Python')
            if verbose:
                print(f'❌ Missing funct7 in Python: {name}')

    # Check instruction count
    if verbose:
        print("\nChecking instruction count...")

    yaml_instructions = yaml_data['instructions']
    isa = RISCVISA()

    yaml_count = len(yaml_instructions)
    python_count = len(isa.instructions)

    if verbose:
        print(f'YAML instructions: {yaml_count}')
        print(f'Python instructions: {python_count}')

    if yaml_count != python_count:
        errors.append(f'Instruction count mismatch: YAML={yaml_count}, Python={python_count}')
        if verbose:
            print('❌ Instruction count mismatch')
    else:
        if verbose:
            print('✅ Instruction counts match')

    return errors

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check consistency between Python and C++ instruction definitions")
    parser.add_argument("--check-yaml", action="store_true",
                       help="Check YAML definition consistency")
    parser.add_argument("--check-enums", action="store_true",
                       help="Check enum value consistency")
    parser.add_argument("--check-all", action="store_true",
                       help="Check all consistency aspects")
    parser.add_argument("--verbose", action="store_true",
                       help="Print detailed output")

    args = parser.parse_args()

    # If --check-all is specified, enable all checks
    if args.check_all:
        args.check_yaml = True
        args.check_enums = True

    errors = []

    if args.check_yaml or args.check_enums:
        errors.extend(check_yaml_consistency(verbose=args.verbose))

    # Report results
    if errors:
        print(f"\nTotal errors: {len(errors)}")
        if args.verbose:
            print("\nDetailed errors:")
            for error in errors:
                print(f"  - {error}")
        sys.exit(1)
    else:
        if args.verbose:
            print("\n✅ All consistency checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()