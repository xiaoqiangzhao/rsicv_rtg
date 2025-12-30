#!/usr/bin/env python3
"""
Sequence pattern generator for RISC-V instruction sequences.
Extends the constraint system to define multi-instruction patterns.
"""

import random
import yaml
from typing import List, Tuple, Optional, Dict, Any, Union
from riscv_isa import RISCVISA, Instruction, InstructionFormat, Registers
from patterns import PatternGenerator, SemanticState, CommentGenerator


class SequenceStep:
    """Represents a single step in a sequence pattern."""

    def __init__(self, step_data: Dict[str, Any], step_index: int):
        self.step_index = step_index
        self.step_type = step_data.get('step_type', 'instruction')
        self.description = step_data.get('description', f'Step {step_index}')

        if self.step_type == 'instruction':
            self._parse_instruction_step(step_data)
        else:
            raise ValueError(f"Unsupported step type: {self.step_type}")

    def _parse_instruction_step(self, step_data: Dict[str, Any]):
        """Parse instruction step configuration."""
        instr_data = step_data.get('instruction', {})
        self.instr_names = instr_data.get('names', [])
        self.instr_weight = instr_data.get('weight', 1.0)

        # Constraints for this step
        self.constraints = step_data.get('constraints', {})

        # Variable definitions for this step
        self.variables = step_data.get('variables', {})

        # Register field specifications
        self.reg_specs = {}
        if 'registers' in self.constraints:
            reg_constraints = self.constraints['registers']
            for reg_field in ['rd', 'rs1', 'rs2']:
                if reg_field in reg_constraints:
                    self.reg_specs[reg_field] = reg_constraints[reg_field]

    def get_instruction_name(self) -> str:
        """Select an instruction name based on weights."""
        if not self.instr_names:
            raise ValueError(f"No instruction names defined for step {self.step_index}")

        # Simple random selection (could be weighted)
        return random.choice(self.instr_names)

    def resolve_register(self, reg_spec: Any, context: Dict[str, Any]) -> int:
        """Resolve a register specification to a concrete register number."""
        if reg_spec is None:
            return 0  # Default to x0

        if isinstance(reg_spec, int):
            return reg_spec

        if isinstance(reg_spec, dict):
            spec_type = reg_spec.get('type')

            if spec_type == 'register':
                # Specific register or from allowed list
                if 'value' in reg_spec:
                    return reg_spec['value']
                elif 'allowed' in reg_spec:
                    allowed = reg_spec['allowed']
                    if allowed:
                        reg = random.choice(allowed)
                        # Check zero exclusion
                        if reg_spec.get('exclude_zero', False) and reg == 0:
                            non_zero = [r for r in allowed if r != 0]
                            if non_zero:
                                reg = random.choice(non_zero)
                        return reg

            elif spec_type == 'variable':
                # Reference to variable defined in sequence
                var_name = reg_spec.get('name')
                if var_name in context.get('variables', {}):
                    return context['variables'][var_name]

            elif spec_type == 'same_as':
                # Same as another register in this step
                other_field = reg_spec.get('field')
                if other_field in self.reg_specs:
                    return self.resolve_register(self.reg_specs[other_field], context)

            elif spec_type == 'different_from':
                # Different from specified registers
                exclude_regs = reg_spec.get('exclude', [])
                exclude = set()
                for reg_ref in exclude_regs:
                    if isinstance(reg_ref, int):
                        exclude.add(reg_ref)
                    elif isinstance(reg_ref, dict) and reg_ref.get('type') == 'variable':
                        var_name = reg_ref.get('name')
                        if var_name in context.get('variables', {}):
                            exclude.add(context['variables'][var_name])

                # Try to find a register not in exclude list
                allowed = reg_spec.get('allowed', list(range(32)))
                candidates = [r for r in allowed if r not in exclude]
                if candidates:
                    return random.choice(candidates)

        # Default: random register 0-31
        return random.randint(0, 31)

    def resolve_immediate(self, instr: Instruction, context: Dict[str, Any]) -> int:
        """Resolve immediate value based on constraints."""
        imm_constraints = self.constraints.get('immediates', {})

        # Determine immediate type based on instruction format
        imm_type = None
        if instr.format == InstructionFormat.I:
            imm_type = 'i_type'
        elif instr.format == InstructionFormat.S:
            imm_type = 's_type'
        elif instr.format == InstructionFormat.B:
            imm_type = 'b_type'
        elif instr.format == InstructionFormat.U:
            imm_type = 'u_type'
        elif instr.format == InstructionFormat.J:
            imm_type = 'j_type'

        if imm_type and imm_type in imm_constraints:
            type_constraints = imm_constraints[imm_type]

            if 'value' in type_constraints:
                return type_constraints['value']

            elif 'allowed_values' in type_constraints:
                allowed = type_constraints['allowed_values']
                if allowed:
                    return random.choice(allowed)

            elif 'min' in type_constraints and 'max' in type_constraints:
                min_val = type_constraints['min']
                max_val = type_constraints['max']

                # Handle alignment
                alignment = type_constraints.get('alignment', 1)
                if alignment > 1:
                    aligned_min = ((min_val + alignment - 1) // alignment) * alignment
                    aligned_max = (max_val // alignment) * alignment
                    if aligned_min > aligned_max:
                        return 0
                    value = random.randint(aligned_min // alignment, aligned_max // alignment) * alignment
                else:
                    value = random.randint(min_val, max_val)

                return value

        # Default: small immediate for I/S type, 0 for others
        if instr.format in [InstructionFormat.I, InstructionFormat.S]:
            return random.randint(-100, 100)
        elif instr.format == InstructionFormat.B:
            return random.choice([-20, -16, -12, -8, -4, 4, 8, 12, 16, 20])
        else:
            return 0

    def generate(self, isa: RISCVISA, pattern_gen: PatternGenerator,
                 context: Dict[str, Any]) -> Tuple[int, str]:
        """Generate this step's instruction."""
        if self.step_type != 'instruction':
            raise ValueError(f"Cannot generate non-instruction step type: {self.step_type}")

        # Get instruction by name
        instr_name = self.get_instruction_name()
        instr = None
        # Search for instruction in ISA
        for i in isa.instructions:
            if i.name == instr_name:
                instr = i
                break
        if instr is None:
            raise ValueError(f"Instruction not found: {instr_name}")

        # Resolve registers
        rd = self.resolve_register(self.reg_specs.get('rd'), context)
        rs1 = self.resolve_register(self.reg_specs.get('rs1'), context)
        rs2 = self.resolve_register(self.reg_specs.get('rs2'), context)

        # Resolve immediate
        imm = self.resolve_immediate(instr, context)

        # Update context with variables defined in this step
        if self.variables:
            for var_name, var_spec in self.variables.items():
                if var_spec.get('type') == 'register':
                    source_field = var_spec.get('source_field')
                    if source_field == 'rd':
                        context.setdefault('variables', {})[var_name] = rd
                    elif source_field == 'rs1':
                        context.setdefault('variables', {})[var_name] = rs1
                    elif source_field == 'rs2':
                        context.setdefault('variables', {})[var_name] = rs2

        # Generate instruction using pattern generator
        encoded = instr.encode(rd=rd, rs1=rs1, rs2=rs2, imm=imm)
        asm = instr.assembly(rd=rd, rs1=rs1, rs2=rs2, imm=imm)

        # Add comment if pattern generator has comment generator
        if hasattr(pattern_gen, '_generate_comment'):
            comment = pattern_gen._generate_comment(instr, rd, rs1, rs2, imm)
            if comment:
                asm = f"{asm}  # {comment}"

        # Record in semantic state
        if hasattr(pattern_gen, '_record_instruction'):
            pattern_gen._record_instruction(instr, rd, rs1, rs2, imm)

        return encoded, asm


class SequencePattern:
    """Represents a complete sequence pattern."""

    def __init__(self, name: str, pattern_data: Dict[str, Any]):
        self.name = name
        self.description = pattern_data.get('description', f'Sequence pattern {name}')
        self.min_length = pattern_data.get('min_length', 1)
        self.max_length = pattern_data.get('max_length', 10)
        self.weight = pattern_data.get('weight', 1.0)

        # Parse steps
        self.steps = []
        steps_data = pattern_data.get('steps', [])
        for i, step_data in enumerate(steps_data):
            step = SequenceStep(step_data, i)
            self.steps.append(step)

        # Global variables for the pattern
        self.global_variables = pattern_data.get('variables', {})

    def generate(self, isa: RISCVISA, pattern_gen: PatternGenerator) -> List[Tuple[int, str]]:
        """Generate the complete sequence."""
        results = []
        context = {'variables': {}}

        # Initialize global variables
        for var_name, var_spec in self.global_variables.items():
            if var_spec.get('type') == 'register':
                # Simple random register for now
                context['variables'][var_name] = random.randint(1, 31)  # Exclude x0

        # Generate each step
        for step in self.steps:
            encoded, asm = step.generate(isa, pattern_gen, context)
            results.append((encoded, asm))

        return results

    def can_generate(self, available_slots: int) -> bool:
        """Check if this pattern can fit within available instruction slots."""
        return len(self.steps) <= available_slots


class SequencePatternLoader:
    """Loads and manages sequence patterns from YAML files."""

    def __init__(self, constraint_file: Optional[str] = None):
        self.patterns: Dict[str, SequencePattern] = {}

        if constraint_file:
            self.load_patterns(constraint_file)

    def load_patterns(self, constraint_file: str):
        """Load sequence patterns from YAML file."""
        with open(constraint_file, 'r') as f:
            data = yaml.safe_load(f)

        sequence_patterns = data.get('sequence_patterns', {})

        for pattern_name, pattern_data in sequence_patterns.items():
            pattern = SequencePattern(pattern_name, pattern_data)
            self.patterns[pattern_name] = pattern

    def get_pattern(self, name: str) -> Optional[SequencePattern]:
        """Get a pattern by name."""
        return self.patterns.get(name)

    def get_all_pattern_names(self) -> List[str]:
        """Get list of all loaded pattern names."""
        return list(self.patterns.keys())

    def get_patterns_by_length(self, max_length: int) -> List[SequencePattern]:
        """Get patterns that can fit within specified length."""
        return [p for p in self.patterns.values() if len(p.steps) <= max_length]

    def select_pattern(self, available_slots: int, weights: Optional[Dict[str, float]] = None,
                      patterns: Optional[Dict[str, SequencePattern]] = None) -> Optional[SequencePattern]:
        """Select a pattern based on weights and available slots.

        Args:
            available_slots: Maximum number of instruction slots available
            weights: Custom weights for pattern selection
            patterns: Specific patterns to choose from (default: all patterns)
        """
        if patterns is None:
            patterns = self.patterns

        # Filter patterns by length
        candidates = []
        for pattern in patterns.values():
            if len(pattern.steps) <= available_slots:
                candidates.append(pattern)

        if not candidates:
            return None

        # Apply custom weights if provided
        if weights:
            weighted_candidates = []
            for pattern in candidates:
                weight = weights.get(pattern.name, pattern.weight)
                weighted_candidates.append((pattern, weight))

            # Weighted random selection
            total_weight = sum(weight for _, weight in weighted_candidates)
            if total_weight <= 0:
                return random.choice(candidates)

            r = random.uniform(0, total_weight)
            cumulative = 0
            for pattern, weight in weighted_candidates:
                cumulative += weight
                if r <= cumulative:
                    return pattern

        # Default: weight-based selection
        total_weight = sum(p.weight for p in candidates)
        if total_weight <= 0:
            return random.choice(candidates)

        r = random.uniform(0, total_weight)
        cumulative = 0
        for pattern in candidates:
            cumulative += pattern.weight
            if r <= cumulative:
                return pattern

        return candidates[0]


class SequencePatternGenerator:
    """Generates instruction sequences using loaded patterns."""

    def __init__(self, isa: RISCVISA, pattern_loader: SequencePatternLoader,
                 pattern_gen: Optional[PatternGenerator] = None):
        self.isa = isa
        self.pattern_loader = pattern_loader
        self.pattern_gen = pattern_gen or PatternGenerator(isa)

    def generate_sequence(self, count: int,
                         pattern_names: Optional[List[str]] = None,
                         pattern_density: float = 0.3) -> List[Tuple[int, str]]:
        """Generate a sequence mixing patterns and random instructions."""
        results = []
        remaining = count

        # Clip density to valid range
        pattern_density = max(0.0, min(1.0, pattern_density))

        # Filter patterns if specific names provided
        available_patterns = {}
        if pattern_names:
            for name in pattern_names:
                pattern = self.pattern_loader.get_pattern(name)
                if pattern:
                    available_patterns[name] = pattern
        else:
            available_patterns = self.pattern_loader.patterns

        while remaining > 0:
            # Decide whether to generate a pattern
            if remaining >= 2 and random.random() < pattern_density and available_patterns:
                # Select a pattern that fits from available patterns
                pattern = self.pattern_loader.select_pattern(remaining, patterns=available_patterns)
                if pattern and len(pattern.steps) <= remaining:
                    # Generate the pattern
                    sequence = pattern.generate(self.isa, self.pattern_gen)
                    results.extend(sequence)
                    remaining -= len(sequence)
                else:
                    # Fallback to random instruction
                    self._add_random_instruction(results)
                    remaining -= 1
            else:
                # Single random instruction
                self._add_random_instruction(results)
                remaining -= 1

        return results[:count]

    def _add_random_instruction(self, results: List[Tuple[int, str]]):
        """Add a random instruction using pattern generator."""
        # Try to use pattern generator's method first (handles semantic state)
        if hasattr(self.pattern_gen, '_generate_single_random_instruction'):
            encoded, asm = self.pattern_gen._generate_single_random_instruction()
            results.append((encoded, asm))
        else:
            # Fallback: generate directly from ISA
            instr = self.isa.get_random_instruction()
            encoded, asm = self.isa.generate_random_instruction(instr)
            results.append((encoded, asm))

    def generate_specific_pattern(self, pattern_name: str) -> List[Tuple[int, str]]:
        """Generate a specific named pattern."""
        pattern = self.pattern_loader.get_pattern(pattern_name)
        if not pattern:
            raise ValueError(f"Pattern not found: {pattern_name}")

        return pattern.generate(self.isa, self.pattern_gen)