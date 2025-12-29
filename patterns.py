#!/usr/bin/env python3
"""
Pattern-based instruction sequence generator for RISC-V.
Implements common instruction patterns and data hazards.
"""

import random
from typing import List, Tuple, Optional, Dict, Any
from riscv_isa import RISCVISA, Instruction, InstructionFormat, Registers


class SemanticState:
    """Tracks semantic state for instruction stream generation."""

    def __init__(self):
        # Register tracking: map register number to last writer instruction index
        self.register_writers: Dict[int, int] = {}  # reg -> instruction index
        self.register_readers: Dict[int, List[int]] = {}  # reg -> list of instruction indices
        # Memory tracking: map base register to access pattern
        self.memory_accesses: Dict[int, List[Tuple[int, int]]] = {}  # base reg -> list of (offset, instr_idx)
        # Control flow tracking
        self.loop_nesting: int = 0
        self.current_loop_counter_reg: Optional[int] = None
        self.branch_targets: Dict[int, int] = {}  # instruction index -> target address
        # Function state
        self.in_function: bool = False
        self.stack_pointer_offset: int = 0
        self.saved_registers: List[int] = []

    def update_register_write(self, reg: int, instr_idx: int):
        """Update state when register is written."""
        self.register_writers[reg] = instr_idx
        if reg not in self.register_readers:
            self.register_readers[reg] = []

    def update_register_read(self, reg: int, instr_idx: int):
        """Update state when register is read."""
        if reg not in self.register_readers:
            self.register_readers[reg] = []
        self.register_readers[reg].append(instr_idx)

    def update_memory_access(self, base_reg: int, offset: int, instr_idx: int):
        """Update state for memory load/store."""
        if base_reg not in self.memory_accesses:
            self.memory_accesses[base_reg] = []
        self.memory_accesses[base_reg].append((offset, instr_idx))

    def enter_loop(self, counter_reg: Optional[int] = None):
        """Enter a loop nesting level."""
        self.loop_nesting += 1
        self.current_loop_counter_reg = counter_reg

    def exit_loop(self):
        """Exit a loop nesting level."""
        self.loop_nesting = max(0, self.loop_nesting - 1)
        if self.loop_nesting == 0:
            self.current_loop_counter_reg = None

    def add_branch_target(self, instr_idx: int, target_addr: int):
        """Record a branch target."""
        self.branch_targets[instr_idx] = target_addr

    def enter_function(self):
        """Enter function scope."""
        self.in_function = True
        self.stack_pointer_offset = 0
        self.saved_registers = []

    def exit_function(self):
        """Exit function scope."""
        self.in_function = False
        self.stack_pointer_offset = 0
        self.saved_registers = []

    def allocate_stack(self, size: int):
        """Allocate stack space."""
        self.stack_pointer_offset += size

    def deallocate_stack(self, size: int):
        """Deallocate stack space."""
        self.stack_pointer_offset = max(0, self.stack_pointer_offset - size)

    def save_register(self, reg: int):
        """Mark register as saved in prologue."""
        if reg not in self.saved_registers:
            self.saved_registers.append(reg)

    def get_last_writer(self, reg: int) -> Optional[int]:
        """Get instruction index of last writer to register, or None."""
        return self.register_writers.get(reg)

    def get_readers(self, reg: int) -> List[int]:
        """Get list of instruction indices that read register."""
        return self.register_readers.get(reg, [])

    def get_memory_access_pattern(self, base_reg: int) -> List[Tuple[int, int]]:
        """Get memory access pattern for base register."""
        return self.memory_accesses.get(base_reg, [])

    def is_in_loop(self) -> bool:
        """Check if currently in a loop."""
        return self.loop_nesting > 0

    def get_current_loop_counter_reg(self) -> Optional[int]:
        """Get current loop counter register, if any."""
        return self.current_loop_counter_reg


class CommentGenerator:
    """Generates semantic comments for instructions based on detail level."""

    def __init__(self, semantic_state: Optional[SemanticState] = None, detail_level: str = "medium"):
        """
        Args:
            semantic_state: SemanticState object tracking context
            detail_level: "minimal", "medium", or "detailed"
        """
        self.semantic_state = semantic_state
        self.detail_level = detail_level.lower()
        if self.detail_level not in ["none", "minimal", "medium", "detailed"]:
            self.detail_level = "medium"

    def generate(self, instr: Instruction, rd: int, rs1: int, rs2: int, imm: int, instr_idx: int) -> Optional[str]:
        """Generate comment for instruction, or None if no comment."""
        if self.semantic_state is None or self.detail_level == "none":
            return None

        comments = []
        # Data dependency comments
        if rd != 0:
            last_writer = self.semantic_state.get_last_writer(rd)
            if last_writer is not None:
                if self.detail_level == "minimal":
                    comments.append(f"[REG_WRITE {rd}]")
                elif self.detail_level == "medium":
                    comments.append(f"reg x{rd} written")
                else:  # detailed
                    comments.append(f"register x{rd} previously written at instruction {last_writer}")
        if rs1 != 0:
            readers = self.semantic_state.get_readers(rs1)
            if self.detail_level == "minimal":
                comments.append(f"[REG_READ {rs1}]")
            elif self.detail_level == "medium":
                comments.append(f"reads x{rs1}")
            else:
                comments.append(f"reads register x{rs1} (read {len(readers)} times previously)")
        if rs2 != 0:
            readers = self.semantic_state.get_readers(rs2)
            if self.detail_level == "minimal":
                comments.append(f"[REG_READ {rs2}]")
            elif self.detail_level == "medium":
                comments.append(f"reads x{rs2}")
            else:
                comments.append(f"reads register x{rs2} (read {len(readers)} times previously)")

        # Memory access comments
        if instr.name in ['lb', 'lh', 'lw', 'lbu', 'lhu']:
            if self.detail_level == "minimal":
                comments.append("[LOAD]")
            elif self.detail_level == "medium":
                comments.append(f"load from x{rs1}+{imm}")
            else:
                accesses = self.semantic_state.get_memory_access_pattern(rs1)
                comments.append(f"load from address x{rs1}+{imm} ({len(accesses)} previous accesses to this base)")
        elif instr.name in ['sb', 'sh', 'sw']:
            if self.detail_level == "minimal":
                comments.append("[STORE]")
            elif self.detail_level == "medium":
                comments.append(f"store to x{rs1}+{imm}")
            else:
                accesses = self.semantic_state.get_memory_access_pattern(rs1)
                comments.append(f"store to address x{rs1}+{imm} ({len(accesses)} previous accesses to this base)")

        # Control flow comments
        if instr.format == InstructionFormat.B:
            if self.detail_level == "minimal":
                comments.append("[BRANCH]")
            elif self.detail_level == "medium":
                comments.append(f"branch target PC{'+' if imm >= 0 else ''}{imm}")
            else:
                target = instr_idx * 4 + imm  # approximate PC
                comments.append(f"branch to PC {target:#x} (offset {imm})")
        elif instr.format == InstructionFormat.J:
            if self.detail_level == "minimal":
                comments.append("[JUMP]")
            elif self.detail_level == "medium":
                comments.append(f"jump target PC{'+' if imm >= 0 else ''}{imm}")
            else:
                target = instr_idx * 4 + imm
                comments.append(f"jump to PC {target:#x} (offset {imm})")

        # Loop context comments
        if self.semantic_state.is_in_loop():
            counter_reg = self.semantic_state.get_current_loop_counter_reg()
            if counter_reg is not None and (rd == counter_reg or rs1 == counter_reg or rs2 == counter_reg):
                if self.detail_level == "minimal":
                    comments.append("[LOOP_CTR]")
                elif self.detail_level == "medium":
                    comments.append(f"loop counter x{counter_reg}")
                else:
                    comments.append(f"uses loop counter register x{counter_reg}")

        # Function context comments
        if self.semantic_state.in_function:
            if self.detail_level == "minimal":
                comments.append("[FUNC]")
            elif self.detail_level == "medium":
                comments.append("in function")
            else:
                comments.append(f"function context, stack offset {self.semantic_state.stack_pointer_offset}")

        if not comments:
            return None

        if self.detail_level == "minimal":
            return " ".join(comments)
        elif self.detail_level == "medium":
            return "; ".join(comments)
        else:  # detailed
            return " | ".join(comments)


class PatternGenerator:
    """Generates instruction sequences with specific patterns and dependencies."""

    def __init__(self, isa: RISCVISA, semantic_state: Optional[SemanticState] = None,
                 comment_generator: Optional[CommentGenerator] = None, comment_detail: str = "medium"):
        self.isa = isa
        self.semantic_state = semantic_state
        self.instr_idx = 0  # Current instruction index for semantic tracking
        if comment_generator is None and semantic_state is not None:
            comment_generator = CommentGenerator(semantic_state, comment_detail)
        self.comment_generator = comment_generator

    def _record_instruction(self, instr: Instruction, rd: int, rs1: int, rs2: int, imm: int):
        """Record instruction in semantic state if available."""
        if self.semantic_state is None:
            return
        # Update register writes
        if rd != 0:
            self.semantic_state.update_register_write(rd, self.instr_idx)
        # Update register reads
        if rs1 != 0:
            self.semantic_state.update_register_read(rs1, self.instr_idx)
        if rs2 != 0:
            self.semantic_state.update_register_read(rs2, self.instr_idx)
        # Update memory accesses for load/store instructions
        if instr.name in ['lb', 'lh', 'lw', 'lbu', 'lhu', 'sb', 'sh', 'sw']:
            self.semantic_state.update_memory_access(rs1, imm, self.instr_idx)
        # Increment instruction index
        self.instr_idx += 1

    def _generate_comment(self, instr: Instruction, rd: int, rs1: int, rs2: int, imm: int) -> Optional[str]:
        """Generate semantic comment for instruction if comment_generator exists."""
        if self.comment_generator is None:
            return None
        # Use current instruction index (before increment) because _record_instruction increments after recording
        comment_idx = self.instr_idx
        return self.comment_generator.generate(instr, rd, rs1, rs2, imm, comment_idx)

    def _generate_single_random_instruction(self, instr: Optional[Instruction] = None) -> Tuple[int, str]:
        """Generate a single random instruction with semantic tracking.

        Args:
            instr: Specific instruction to generate. If None, selects random instruction.
        """
        if instr is None:
            instr = self.isa.get_random_instruction()

        # Generate random registers
        rd = Registers.random()
        rs1 = Registers.random()
        rs2 = Registers.random()
        imm = 0

        # Special handling for certain instructions
        if instr.name in ['ebreak', 'ecall']:
            # These have no registers or immediates
            rd = rs1 = rs2 = imm = 0
        elif instr.format == InstructionFormat.R:
            # No immediate for R-type
            imm = 0
        elif instr.format == InstructionFormat.U or instr.format == InstructionFormat.J:
            # Only rd and immediate
            rs1 = rs2 = 0
            imm = self._get_immediate(instr)
        elif instr.format == InstructionFormat.I:
            # Only rd, rs1, and immediate
            rs2 = 0
            imm = self._get_immediate(instr)
        elif instr.format == InstructionFormat.S or instr.format == InstructionFormat.B:
            # Only rs1, rs2, and immediate
            rd = 0
            imm = self._get_immediate(instr)

        # Encode instruction
        encoded = instr.encode(rd=rd, rs1=rs1, rs2=rs2, imm=imm)
        asm = instr.assembly(rd=rd, rs1=rs1, rs2=rs2, imm=imm)

        # Record instruction in semantic state
        self._record_instruction(instr, rd, rs1, rs2, imm)

        # Generate comment
        comment = self._generate_comment(instr, rd, rs1, rs2, imm)
        if comment:
            asm = f"{asm}  # {comment}"

        return encoded, asm

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
        results = []
        for _ in range(count):
            results.append(self._generate_single_random_instruction())
        return results

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
        self._record_instruction(load, rd, rs1, 0, load_imm)
        load_comment = self._generate_comment(load, rd, rs1, 0, load_imm)
        if load_comment:
            load_asm = f"{load_asm}  # {load_comment}"

        store_encoded = store.encode(rd=0, rs1=store_rs1, rs2=rs2, imm=store_imm)
        store_asm = store.assembly(rd=0, rs1=store_rs1, rs2=rs2, imm=store_imm)
        self._record_instruction(store, 0, store_rs1, rs2, store_imm)
        store_comment = self._generate_comment(store, 0, store_rs1, rs2, store_imm)
        if store_comment:
            store_asm = f"{store_asm}  # {store_comment}"

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
        self._record_instruction(instr1, rd, rs1, rs2, imm)
        comment1 = self._generate_comment(instr1, rd, rs1, rs2, imm)
        if comment1:
            asm1 = f"{asm1}  # {comment1}"

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
        self._record_instruction(instr2, rd2, rs1_2, rs2_2, imm2)
        comment2 = self._generate_comment(instr2, rd2, rs1_2, rs2_2, imm2)
        if comment2:
            asm2 = f"{asm2}  # {comment2}"

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
        self._record_instruction(instr1, rd, rs1, rs2, imm)

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
        self._record_instruction(instr2, rd2, rs1_2, rs2_2, imm2)
        comment2 = self._generate_comment(instr2, rd2, rs1_2, rs2_2, imm2)
        if comment2:
            asm2 = f"{asm2}  # {comment2}"

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
            encoded, asm = self._generate_single_random_instruction(instr)
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
                encoded, asm = self._generate_single_random_instruction(instr)
                instructions.append((encoded, asm))
            else:
                # Fallback to regular instruction
                encoded, asm = self._generate_single_random_instruction()
                instructions.append((encoded, asm))
        else:
            # Add regular instruction
            encoded, asm = self._generate_single_random_instruction()
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
                    encoded, asm = self._generate_single_random_instruction()
                    result.append((encoded, asm))
                    remaining -= 1
            else:
                # Single random instruction
                encoded, asm = self._generate_single_random_instruction()
                result.append((encoded, asm))
                remaining -= 1

        return result[:count]