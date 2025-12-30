#!/usr/bin/env python3
"""
Example constraint loader for RISC-V instruction constraints.
Demonstrates how to load and apply constraint YAML files.
"""

import yaml
import random
from typing import Dict, List, Optional, Any, Union


class ConstraintLoader:
    """Loads and manages instruction constraints from YAML files."""

    def __init__(self, constraint_file: str):
        """Load constraints from YAML file."""
        with open(constraint_file, 'r') as f:
            self.raw_constraints = yaml.safe_load(f)

        # Process constraints into a flattened structure
        self.constraints = self._process_constraints()

    def _process_constraints(self) -> Dict[str, Dict[str, Any]]:
        """Process constraints hierarchy into per-instruction constraints."""
        # Start with global constraints applied to all instructions
        all_instructions = self._get_all_instruction_names()
        processed = {}

        # Get global constraints
        global_cons = self.raw_constraints.get('global_constraints', {})

        # Initialize all instructions with global constraints
        for instr in all_instructions:
            processed[instr] = self._deep_copy_constraints(global_cons)

        # Apply instruction groups (in order of definition)
        groups = self.raw_constraints.get('instruction_groups', {})
        for group_name, group_data in groups.items():
            instructions = group_data.get('instructions', [])
            group_constraints = group_data.get('constraints', {})

            for instr in instructions:
                if instr in processed:
                    self._merge_constraints(processed[instr], group_constraints)

        # Apply instruction overrides (highest precedence)
        overrides = self.raw_constraints.get('instruction_overrides', {})
        for instr_name, instr_data in overrides.items():
            if instr_name in processed:
                instr_constraints = instr_data.get('constraints', {})
                self._merge_constraints(processed[instr_name], instr_constraints)

        return processed

    def _get_all_instruction_names(self) -> List[str]:
        """Get list of all RISC-V instruction names (simplified)."""
        # In a real implementation, this would come from the ISA
        return [
            # R-type
            "add", "sub", "xor", "or", "and", "sll", "srl", "sra", "slt", "sltu",
            # I-type
            "addi", "xori", "ori", "andi", "slli", "srli", "srai", "slti", "sltiu",
            "lb", "lh", "lw", "lbu", "lhu", "jalr",
            # S-type
            "sb", "sh", "sw",
            # B-type
            "beq", "bne", "blt", "bge", "bltu", "bgeu",
            # U-type
            "lui", "auipc",
            # J-type
            "jal",
            # Special
            "ecall", "ebreak"
        ]

    def _deep_copy_constraints(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of constraints dictionary."""
        # Simple deep copy for demonstration
        # In production, use copy.deepcopy()
        if not constraints:
            return {}

        result = {}
        for key, value in constraints.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_constraints(value)
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    def _merge_constraints(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Merge source constraints into target (source overrides)."""
        for key, value in source.items():
            if key == 'weight' and 'weight' in target:
                # Multiply weights
                target[key] = target[key] * value
            elif isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively merge dictionaries
                self._merge_constraints(target[key], value)
            else:
                # Replace other values
                target[key] = value

    def get_constraints(self, instruction_name: str) -> Optional[Dict[str, Any]]:
        """Get constraints for a specific instruction."""
        return self.constraints.get(instruction_name)

    def get_register_constraints(self, instruction_name: str) -> Optional[Dict[str, Any]]:
        """Get register constraints for an instruction."""
        instr_constraints = self.get_constraints(instruction_name)
        if instr_constraints:
            return instr_constraints.get('registers')
        return None

    def get_immediate_constraints(self, instruction_name: str,
                                  imm_type: str = None) -> Optional[Dict[str, Any]]:
        """Get immediate constraints for an instruction."""
        instr_constraints = self.get_constraints(instruction_name)
        if instr_constraints and 'immediates' in instr_constraints:
            immediates = instr_constraints['immediates']
            if imm_type and imm_type in immediates:
                return immediates[imm_type]
            return immediates
        return None

    def get_weight(self, instruction_name: str) -> float:
        """Get weight (relative probability) for an instruction."""
        instr_constraints = self.get_constraints(instruction_name)
        if instr_constraints and 'weight' in instr_constraints:
            return instr_constraints['weight']
        return 1.0

    def select_register(self, register_constraints: Dict[str, Any],
                        reg_type: str = 'rd') -> int:
        """Select a register based on constraints."""
        if not register_constraints:
            return random.randint(0, 31)

        # Check for allowed list
        allowed_key = f"{reg_type}_allowed"
        if allowed_key in register_constraints:
            allowed = register_constraints[allowed_key]
            if allowed:
                reg = random.choice(allowed)

                # Check zero exclusion
                zero_exclude_key = f"exclude_zero_{reg_type}"
                if register_constraints.get(zero_exclude_key, False) and reg == 0:
                    # Try to find non-zero register
                    non_zero = [r for r in allowed if r != 0]
                    if non_zero:
                        reg = random.choice(non_zero)
                    # If all allowed are zero, return zero (shouldn't happen)

                return reg

        # Check for range
        range_key = f"{reg_type}_range"
        if range_key in register_constraints:
            range_dict = register_constraints[range_key]
            min_reg = range_dict.get('min', 0)
            max_reg = range_dict.get('max', 31)

            reg = random.randint(min_reg, max_reg)

            # Check zero exclusion
            zero_exclude_key = f"exclude_zero_{reg_type}"
            if register_constraints.get(zero_exclude_key, False) and reg == 0:
                # Try again (could loop if range is only zero)
                while reg == 0:
                    reg = random.randint(min_reg, max_reg)

            return reg

        # Default: random register 0-31
        return random.randint(0, 31)

    def generate_immediate(self, immediate_constraints: Dict[str, Any]) -> int:
        """Generate an immediate value based on constraints."""
        if not immediate_constraints:
            # Default small range for demonstration
            return random.randint(-100, 100)

        # Check for specific type constraints
        if 'min' in immediate_constraints and 'max' in immediate_constraints:
            min_val = immediate_constraints['min']
            max_val = immediate_constraints['max']

            # Handle alignment
            alignment = immediate_constraints.get('alignment', 1)
            if alignment > 1:
                # Generate aligned value
                aligned_min = ((min_val + alignment - 1) // alignment) * alignment
                aligned_max = (max_val // alignment) * alignment
                if aligned_min > aligned_max:
                    return 0
                value = random.randint(aligned_min // alignment, aligned_max // alignment) * alignment
            else:
                value = random.randint(min_val, max_val)

            return value

        # Check for allowed values list
        elif 'allowed_values' in immediate_constraints:
            allowed = immediate_constraints['allowed_values']
            if allowed:
                return random.choice(allowed)

        # Default fallback
        return random.randint(-100, 100)


def demonstrate_constraint_loading():
    """Demonstrate loading and using constraints."""
    print("=== RISC-V Constraint Loader Demonstration ===\n")

    # Load example constraints
    try:
        loader = ConstraintLoader("example_constraint.yaml")
        print("✓ Successfully loaded constraints from example_constraint.yaml\n")
    except FileNotFoundError:
        print("Error: example_constraint.yaml not found")
        print("Please run from the isa_constraint directory")
        return

    # Demonstrate getting constraints for specific instructions
    test_instructions = ["add", "addi", "lw", "beq", "lui", "ecall"]

    for instr in test_instructions:
        print(f"\n--- Constraints for '{instr}' ---")

        # Get all constraints
        constraints = loader.get_constraints(instr)
        if not constraints:
            print("  No constraints found")
            continue

        # Show register constraints
        reg_constraints = loader.get_register_constraints(instr)
        if reg_constraints:
            print(f"  Register constraints:")
            for key, value in reg_constraints.items():
                if isinstance(value, list) and len(value) > 10:
                    print(f"    {key}: [{value[0]}, {value[1]}, ..., {value[-1]}] ({len(value)} items)")
                elif isinstance(value, dict):
                    print(f"    {key}: {value}")
                else:
                    print(f"    {key}: {value}")

        # Show immediate constraints
        imm_constraints = loader.get_immediate_constraints(instr)
        if imm_constraints:
            print(f"  Immediate constraints:")
            for key, value in imm_constraints.items():
                if isinstance(value, dict):
                    print(f"    {key}: {value}")
                else:
                    print(f"    {key}: {value}")

        # Show weight
        weight = loader.get_weight(instr)
        print(f"  Weight: {weight}")

        # Demonstrate register selection
        if reg_constraints:
            print(f"  Example register selections:")
            for reg_type in ['rd', 'rs1', 'rs2']:
                # Only show if relevant for this instruction
                # (e.g., stores don't have rd, etc.)
                if any(key.startswith(reg_type) for key in reg_constraints.keys()):
                    reg = loader.select_register(reg_constraints, reg_type)
                    print(f"    {reg_type}: x{reg}")

        # Demonstrate immediate generation
        if imm_constraints:
            # Determine immediate type based on instruction
            imm_type = None
            if instr in ['addi', 'xori', 'ori', 'andi', 'lb', 'lh', 'lw', 'lbu', 'lhu', 'jalr', 'slli', 'srli', 'srai', 'slti', 'sltiu']:
                imm_type = 'i_type'
            elif instr in ['sb', 'sh', 'sw']:
                imm_type = 's_type'
            elif instr in ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']:
                imm_type = 'b_type'
            elif instr in ['lui', 'auipc']:
                imm_type = 'u_type'
            elif instr in ['jal']:
                imm_type = 'j_type'

            if imm_type:
                type_constraints = loader.get_immediate_constraints(instr, imm_type)
                if type_constraints:
                    imm = loader.generate_immediate(type_constraints)
                    print(f"  Example immediate ({imm_type}): {imm}")

    print("\n=== End of Demonstration ===")


if __name__ == "__main__":
    demonstrate_constraint_loading()