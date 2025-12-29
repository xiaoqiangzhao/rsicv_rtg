#!/usr/bin/env python3
"""
Pattern-based instruction sequence generator for RISC-V.
Implements common instruction patterns and data hazards.
"""

import random
from typing import List, Tuple, Optional, Dict, Any
from riscv_isa import RISCVISA, Instruction, InstructionFormat, Registers


class PatternGenerator:
    """Generates instruction sequences with specific patterns and dependencies."""

    def __init__(self, isa: RISCVISA):
        self.isa = isa

    def _get_immediate(self, instr):
        """Get a random immediate appropriate for the instruction."""
        if instr.imm_gen:
            return instr.imm_gen()
        # Default fallback based on format
        if instr.format == InstructionFormat.R:
            return 0
        elif instr.format == InstructionFormat.I:
            return random.randint(-2048, 2047)
        elif instr.format == InstructionFormat.S:
            return random.randint(-2048, 2047)
        elif instr.format == InstructionFormat.B:
            return random.randint(-4096, 4094) & ~1
        elif instr.format == InstructionFormat.U:
            return random.randint(-524288, 524287)
        elif instr.format == InstructionFormat.J:
            return random.randint(-1048576, 1048574) & ~1
        else:
            return 0

    def generate_random_sequence(self, count: int) -> List[Tuple[int, str]]:
        """Generate random sequence of instructions (no specific pattern)."""
        return self.isa.generate_random(count)

    def generate_load_store_pair(self, base_address: int = 0) -> List[Tuple[int, str]]:
        """Generate a load followed by a store pattern.
        Pattern: lw rd, offset(rs1) ; sw rd, offset2(rs2)
        Creates dependency through rd register."""
        # Get load instructions (lw, lh, lb, lhu, lbu)
        load_instrs = [instr for instr in self.isa.instructions
                      if instr.name in ['lw', 'lh', 'lb', 'lhu', 'lbu']]
        if not load_instrs:
            load_instrs = self.isa.get_instructions_by_format(InstructionFormat.I)

        # Get store instructions (sw, sh, sb)
        store_instrs = [instr for instr in self.isa.instructions
                       if instr.name in ['sw', 'sh', 'sb']]
        if not store_instrs:
            store_instrs = self.isa.get_instructions_by_format(InstructionFormat.S)

        if not load_instrs or not store_instrs:
            return self.generate_random_sequence(2)

        # Choose random load and store
        load = random.choice(load_instrs)
        store = random.choice(store_instrs)

        # Generate registers: rd for load, rs2 for store (same register creates dependency)
        rd = Registers.random(exclude_zero=True)
        rs1 = Registers.random(exclude_zero=True)
        rs2 = rd  # Same register creates dependency
        # For store, we need rs1 for base address (can be same or different)
        store_rs1 = Registers.random(exclude_zero=True)

        # Generate immediates using ISA's offset range if available
        offset_min = getattr(self.isa, 'load_store_offset_min', -2048)
        offset_max = getattr(self.isa, 'load_store_offset_max', 2047)
        load_imm = random.randint(offset_min, offset_max)
        store_imm = random.randint(offset_min, offset_max)

        # Encode instructions
        load_encoded = load.encode(rd=rd, rs1=rs1, rs2=0, imm=load_imm)
        load_asm = load.assembly(rd=rd, rs1=rs1, rs2=0, imm=load_imm)

        store_encoded = store.encode(rd=0, rs1=store_rs1, rs2=rs2, imm=store_imm)
        store_asm = store.assembly(rd=0, rs1=store_rs1, rs2=rs2, imm=store_imm)

        return [(load_encoded, load_asm), (store_encoded, store_asm)]

    def generate_raw_hazard(self) -> List[Tuple[int, str]]:
        """Generate RAW (Read After Write) hazard.
        Pattern: instr1 writes to rd, instr2 reads from same register as rs1/rs2."""
        # Get instructions that write to registers (most instructions except stores/branches)
        write_instrs = [instr for instr in self.isa.instructions
                       if instr.format not in [InstructionFormat.S, InstructionFormat.B]]
        read_instrs = [instr for instr in self.isa.instructions
                      if instr.format not in [InstructionFormat.U, InstructionFormat.J]]

        if len(write_instrs) < 2:
            return self.generate_random_sequence(2)

        # First instruction writes to rd
        instr1 = random.choice(write_instrs)
        rd = Registers.random(exclude_zero=True)
        rs1 = Registers.random(exclude_zero=True)
        rs2 = Registers.random(exclude_zero=True)

        # Generate first instruction
        if instr1.format == InstructionFormat.R:
            imm = 0
        elif instr1.format == InstructionFormat.I:
            imm = self._get_immediate(instr1)
            rs2 = 0
        elif instr1.format == InstructionFormat.U:
            imm = self._get_immediate(instr1)
            rs1 = rs2 = 0
        else:
            imm = 0

        encoded1 = instr1.encode(rd=rd, rs1=rs1, rs2=rs2, imm=imm)
        asm1 = instr1.assembly(rd=rd, rs1=rs1, rs2=rs2, imm=imm)

        # Second instruction reads from the same register (RAW hazard)
        instr2 = random.choice(read_instrs)
        # Choose whether to use rd as rs1 or rs2
        use_as_rs1 = random.choice([True, False])

        if use_as_rs1:
            rs1_2 = rd
            rs2_2 = Registers.random(exclude_zero=True)
        else:
            rs1_2 = Registers.random(exclude_zero=True)
            rs2_2 = rd

        rd2 = Registers.random(exclude_zero=True) if instr2.format not in [InstructionFormat.S, InstructionFormat.B] else 0

        # Generate second instruction
        if instr2.format == InstructionFormat.R:
            imm2 = 0
        elif instr2.format == InstructionFormat.I:
            imm2 = self._get_immediate(instr2)
            rs2_2 = 0
        elif instr2.format == InstructionFormat.S:
            imm2 = self._get_immediate(instr2)
            rd2 = 0
        elif instr2.format == InstructionFormat.B:
            imm2 = self._get_immediate(instr2)
            rd2 = 0
        else:
            imm2 = 0

        encoded2 = instr2.encode(rd=rd2, rs1=rs1_2, rs2=rs2_2, imm=imm2)
        asm2 = instr2.assembly(rd=rd2, rs1=rs1_2, rs2=rs2_2, imm=imm2)

        return [(encoded1, asm1), (encoded2, asm2)]

    def generate_war_hazard(self) -> List[Tuple[int, str]]:
        """Generate WAR (Write After Read) hazard.
        Pattern: instr1 reads from register, instr2 writes to same register."""
        # Similar to RAW but reversed order of operations
        read_instrs = [instr for instr in self.isa.instructions
                      if instr.format not in [InstructionFormat.U, InstructionFormat.J]]
        write_instrs = [instr for instr in self.isa.instructions
                       if instr.format not in [InstructionFormat.S, InstructionFormat.B]]

        if len(read_instrs) < 2:
            return self.generate_random_sequence(2)

        # First instruction reads from register
        instr1 = random.choice(read_instrs)
        hazard_reg = Registers.random(exclude_zero=True)

        # Choose whether hazard_reg is rs1 or rs2 for first instruction
        use_as_rs1 = random.choice([True, False])

        if use_as_rs1:
            rs1 = hazard_reg
            rs2 = Registers.random(exclude_zero=True)
        else:
            rs1 = Registers.random(exclude_zero=True)
            rs2 = hazard_reg

        rd = Registers.random(exclude_zero=True) if instr1.format not in [InstructionFormat.S, InstructionFormat.B] else 0

        # Generate first instruction
        if instr1.format == InstructionFormat.R:
            imm = 0
        elif instr1.format == InstructionFormat.I:
            imm = self._get_immediate(instr1)
            rs2 = 0
        elif instr1.format == InstructionFormat.S:
            imm = self._get_immediate(instr1)
            rd = 0
        elif instr1.format == InstructionFormat.B:
            imm = self._get_immediate(instr1)
            rd = 0
        else:
            imm = 0

        encoded1 = instr1.encode(rd=rd, rs1=rs1, rs2=rs2, imm=imm)
        asm1 = instr1.assembly(rd=rd, rs1=rs1, rs2=rs2, imm=imm)

        # Second instruction writes to the same register (WAR hazard)
        instr2 = random.choice(write_instrs)
        rd2 = hazard_reg  # Write to same register

        rs1_2 = Registers.random(exclude_zero=True)
        rs2_2 = Registers.random(exclude_zero=True)

        # Generate second instruction
        if instr2.format == InstructionFormat.R:
            imm2 = 0
        elif instr2.format == InstructionFormat.I:
            imm2 = self._get_immediate(instr2)
            rs2_2 = 0
        elif instr2.format == InstructionFormat.U:
            imm2 = self._get_immediate(instr2)
            rs1_2 = rs2_2 = 0
        else:
            imm2 = 0

        encoded2 = instr2.encode(rd=rd2, rs1=rs1_2, rs2=rs2_2, imm=imm2)
        asm2 = instr2.assembly(rd=rd2, rs1=rs1_2, rs2=rs2_2, imm=imm2)

        return [(encoded1, asm1), (encoded2, asm2)]

    def generate_waw_hazard(self) -> List[Tuple[int, str]]:
        """Generate WAW (Write After Write) hazard.
        Pattern: Two instructions write to the same register."""
        write_instrs = [instr for instr in self.isa.instructions
                       if instr.format not in [InstructionFormat.S, InstructionFormat.B]]

        if len(write_instrs) < 2:
            return self.generate_random_sequence(2)

        # Choose two write instructions
        instr1 = random.choice(write_instrs)
        instr2 = random.choice([instr for instr in write_instrs if instr != instr1])

        # Same register for both
        hazard_reg = Registers.random(exclude_zero=True)

        # Generate first instruction
        rs1_1 = Registers.random(exclude_zero=True)
        rs2_1 = Registers.random(exclude_zero=True)

        if instr1.format == InstructionFormat.R:
            imm1 = 0
        elif instr1.format == InstructionFormat.I:
            imm1 = self._get_immediate(instr1)
            rs2_1 = 0
        elif instr1.format == InstructionFormat.U:
            imm1 = self._get_immediate(instr1)
            rs1_1 = rs2_1 = 0
        else:
            imm1 = 0

        encoded1 = instr1.encode(rd=hazard_reg, rs1=rs1_1, rs2=rs2_1, imm=imm1)
        asm1 = instr1.assembly(rd=hazard_reg, rs1=rs1_1, rs2=rs2_1, imm=imm1)

        # Generate second instruction (writes to same register)
        rs1_2 = Registers.random(exclude_zero=True)
        rs2_2 = Registers.random(exclude_zero=True)

        if instr2.format == InstructionFormat.R:
            imm2 = 0
        elif instr2.format == InstructionFormat.I:
            imm2 = self._get_immediate(instr2)
            rs2_2 = 0
        elif instr2.format == InstructionFormat.U:
            imm2 = self._get_immediate(instr2)
            rs1_2 = rs2_2 = 0
        else:
            imm2 = 0

        encoded2 = instr2.encode(rd=hazard_reg, rs1=rs1_2, rs2=rs2_2, imm=imm2)
        asm2 = instr2.assembly(rd=hazard_reg, rs1=rs1_2, rs2=rs2_2, imm=imm2)

        return [(encoded1, asm1), (encoded2, asm2)]

    def generate_basic_block(self, size: int = 5) -> List[Tuple[int, str]]:
        """Generate a basic block (sequence without branches).
        Optionally ends with a branch/jump."""
        if size < 2:
            return self.generate_random_sequence(size)

        instructions = []
        # Generate size-1 regular instructions
        for _ in range(size - 1):
            instr = self.isa.get_random_instruction()
            # Avoid branches/jumps in the middle
            while instr.format in [InstructionFormat.B, InstructionFormat.J]:
                instr = self.isa.get_random_instruction()
            encoded, asm = instr.generate_random()
            instructions.append((encoded, asm))

        # Possibly add a branch/jump at the end
        if random.random() > 0.5:
            branch_instrs = self.isa.get_instructions_by_format(InstructionFormat.B)
            jump_instrs = self.isa.get_instructions_by_format(InstructionFormat.J)
            if branch_instrs or jump_instrs:
                if branch_instrs and (not jump_instrs or random.random() > 0.5):
                    instr = random.choice(branch_instrs)
                else:
                    instr = random.choice(jump_instrs)
                encoded, asm = instr.generate_random()
                instructions.append((encoded, asm))
            else:
                # Fallback to regular instruction
                instr = self.isa.get_random_instruction()
                encoded, asm = instr.generate_random()
                instructions.append((encoded, asm))
        else:
            # Add regular instruction
            instr = self.isa.get_random_instruction()
            encoded, asm = instr.generate_random()
            instructions.append((encoded, asm))

        return instructions

    def generate_mixed_patterns(self, count: int,
                               patterns: List[str] = None,
                               density: float = 0.3) -> List[Tuple[int, str]]:
        """Generate mixed sequence with various patterns.

        Args:
            count: Number of instructions to generate
            patterns: List of pattern types to include
            density: Probability of generating a pattern (0.0-1.0)
        """
        if patterns is None:
            patterns = ['random', 'load_store', 'raw', 'war', 'waw']

        # Clip density to valid range
        density = max(0.0, min(1.0, density))

        result = []
        remaining = count

        while remaining > 0:
            if remaining >= 2 and random.random() < density:
                # Generate a pattern
                pattern_type = random.choice(patterns)
                if pattern_type == 'load_store' and remaining >= 2:
                    pair = self.generate_load_store_pair()
                    result.extend(pair)
                    remaining -= 2
                elif pattern_type == 'raw' and remaining >= 2:
                    pair = self.generate_raw_hazard()
                    result.extend(pair)
                    remaining -= 2
                elif pattern_type == 'war' and remaining >= 2:
                    pair = self.generate_war_hazard()
                    result.extend(pair)
                    remaining -= 2
                elif pattern_type == 'waw' and remaining >= 2:
                    pair = self.generate_waw_hazard()
                    result.extend(pair)
                    remaining -= 2
                else:
                    # Fallback to random
                    instr = self.isa.get_random_instruction()
                    encoded, asm = instr.generate_random()
                    result.append((encoded, asm))
                    remaining -= 1
            else:
                # Single random instruction
                instr = self.isa.get_random_instruction()
                encoded, asm = instr.generate_random()
                result.append((encoded, asm))
                remaining -= 1

        return result[:count]