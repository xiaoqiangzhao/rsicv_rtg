#!/usr/bin/env python3
"""
RISC-V ISA Random Instruction Generator
Core classes for RISC-V instruction formats and random generation.
"""

import random
import struct
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any


class Registers(Enum):
    """RISC-V integer registers x0-x31."""
    ZERO = 0
    RA = 1
    SP = 2
    GP = 3
    TP = 4
    T0 = 5
    T1 = 6
    T2 = 7
    S0 = 8
    S1 = 9
    A0 = 10
    A1 = 11
    A2 = 12
    A3 = 13
    A4 = 14
    A5 = 15
    A6 = 16
    A7 = 17
    S2 = 18
    S3 = 19
    S4 = 20
    S5 = 21
    S6 = 22
    S7 = 23
    S8 = 24
    S9 = 25
    S10 = 26
    S11 = 27
    T3 = 28
    T4 = 29
    T5 = 30
    T6 = 31

    @staticmethod
    def random(exclude_zero: bool = False) -> int:
        """Return a random register number (0-31)."""
        if exclude_zero:
            return random.randint(1, 31)
        return random.randint(0, 31)

    @staticmethod
    def random_range(min_reg: int, max_reg: int, exclude_zero: bool = False) -> int:
        """Return a random register number within [min_reg, max_reg] inclusive."""
        if min_reg < 0 or max_reg > 31 or min_reg > max_reg:
            raise ValueError(f"Invalid register range [{min_reg}, {max_reg}]. Must be within 0-31.")
        if exclude_zero and min_reg == 0 and max_reg == 0:
            raise ValueError("Cannot exclude zero register when range is [0, 0].")

        # Generate random register in range
        reg = random.randint(min_reg, max_reg)
        if exclude_zero and reg == 0:
            # If zero is selected and excluded, try again (could be infinite if range only contains zero)
            # But we already checked above, so range must contain non-zero registers
            while reg == 0:
                reg = random.randint(min_reg, max_reg)
        return reg

    @staticmethod
    def random_from_list(allowed_registers: List[int]) -> int:
        """Return a random register number from allowed list."""
        if not allowed_registers:
            raise ValueError("Allowed registers list cannot be empty.")
        return random.choice(allowed_registers)


class InstructionFormat(Enum):
    """RISC-V instruction formats."""
    R = "R"  # register-register
    I = "I"  # immediate
    S = "S"  # store
    B = "B"  # branch
    U = "U"  # upper immediate
    J = "J"  # jump


class Instruction:
    """Base class for RISC-V instructions."""

    def __init__(self, name: str, fmt: InstructionFormat, opcode: int,
                 funct3: Optional[int] = None, funct7: Optional[int] = None,
                 imm_gen=None):
        self.name = name
        self.format = fmt
        self.opcode = opcode
        self.funct3 = funct3
        self.funct7 = funct7
        self.imm_gen = imm_gen  # function that returns random immediate

    def encode(self, rd: int, rs1: int, rs2: int, imm: int = 0) -> int:
        """Encode instruction into 32-bit word."""
        if self.format == InstructionFormat.R:
            # R-type: funct7(31:25), rs2(24:20), rs1(19:15), funct3(14:12), rd(11:7), opcode(6:0)
            return ((self.funct7 & 0x7f) << 25) | ((rs2 & 0x1f) << 20) | \
                   ((rs1 & 0x1f) << 15) | ((self.funct3 & 0x7) << 12) | \
                   ((rd & 0x1f) << 7) | (self.opcode & 0x7f)
        elif self.format == InstructionFormat.I:
            # I-type: imm[11:0](31:20), rs1(19:15), funct3(14:12), rd(11:7), opcode(6:0)
            imm12 = imm & 0xfff
            return ((imm12 & 0xfff) << 20) | ((rs1 & 0x1f) << 15) | \
                   ((self.funct3 & 0x7) << 12) | ((rd & 0x1f) << 7) | \
                   (self.opcode & 0x7f)
        elif self.format == InstructionFormat.S:
            # S-type: imm[11:5](31:25), rs2(24:20), rs1(19:15), funct3(14:12), imm[4:0](11:7), opcode(6:0)
            imm11_5 = (imm >> 5) & 0x7f
            imm4_0 = imm & 0x1f
            return ((imm11_5 & 0x7f) << 25) | ((rs2 & 0x1f) << 20) | \
                   ((rs1 & 0x1f) << 15) | ((self.funct3 & 0x7) << 12) | \
                   ((imm4_0 & 0x1f) << 7) | (self.opcode & 0x7f)
        elif self.format == InstructionFormat.B:
            # B-type: imm[12|10:5](31:25), rs2(24:20), rs1(19:15), funct3(14:12), imm[4:1|11](11:7), opcode(6:0)
            imm12 = (imm >> 12) & 0x1
            imm10_5 = (imm >> 5) & 0x3f
            imm4_1 = (imm >> 1) & 0xf
            imm11 = (imm >> 11) & 0x1
            return ((imm12 << 6 | imm10_5) << 25) | ((rs2 & 0x1f) << 20) | \
                   ((rs1 & 0x1f) << 15) | ((self.funct3 & 0x7) << 12) | \
                   ((imm4_1 << 1 | imm11) << 7) | (self.opcode & 0x7f)
        elif self.format == InstructionFormat.U:
            # U-type: imm[31:12](31:12), rd(11:7), opcode(6:0)
            imm31_12 = (imm >> 12) & 0xfffff
            return ((imm31_12 & 0xfffff) << 12) | ((rd & 0x1f) << 7) | \
                   (self.opcode & 0x7f)
        elif self.format == InstructionFormat.J:
            # J-type: imm[20|10:1|11|19:12](31:12), rd(11:7), opcode(6:0)
            imm20 = (imm >> 20) & 0x1
            imm10_1 = (imm >> 1) & 0x3ff
            imm11 = (imm >> 11) & 0x1
            imm19_12 = (imm >> 12) & 0xff
            imm_encoded = (imm20 << 19) | (imm10_1 << 9) | (imm11 << 8) | imm19_12
            return ((imm_encoded & 0xfffff) << 12) | ((rd & 0x1f) << 7) | \
                   (self.opcode & 0x7f)
        else:
            raise ValueError(f"Unknown format: {self.format}")

    def generate_random(self) -> Tuple[int, str]:
        """Generate random instance of this instruction.
        Returns (encoded_instruction, assembly_string)."""
        rd = Registers.random()
        rs1 = Registers.random()
        rs2 = Registers.random()
        imm = 0

        if self.imm_gen:
            imm = self.imm_gen()

        # Special handling for certain instructions
        if self.name in ['ebreak', 'ecall']:
            # These have no registers or immediates
            rd = rs1 = rs2 = imm = 0
        elif self.format == InstructionFormat.R:
            # No immediate for R-type
            imm = 0
        elif self.format == InstructionFormat.U or self.format == InstructionFormat.J:
            # Only rd and immediate
            rs1 = rs2 = 0
        elif self.format == InstructionFormat.I:
            # Only rd, rs1, and immediate
            rs2 = 0
        elif self.format == InstructionFormat.S or self.format == InstructionFormat.B:
            # Only rs1, rs2, and immediate
            rd = 0

        encoded = self.encode(rd, rs1, rs2, imm)
        asm = self.assembly(rd, rs1, rs2, imm)
        return encoded, asm

    def generate_with_registers(self, rd: Optional[int] = None, rs1: Optional[int] = None,
                                rs2: Optional[int] = None, imm: Optional[int] = None) -> Tuple[int, str]:
        """Generate instruction with specified registers/immediate (or random if None).

        Args:
            rd: Destination register (0-31). If None, random.
            rs1: Source register 1 (0-31). If None, random.
            rs2: Source register 2 (0-31). If None, random.
            imm: Immediate value. If None, uses instruction's immediate generator if available, else 0.

        Returns:
            (encoded_instruction, assembly_string)
        """
        # Generate random registers if not provided
        if rd is None:
            rd = Registers.random()
        if rs1 is None:
            rs1 = Registers.random()
        if rs2 is None:
            rs2 = Registers.random()
        if imm is None:
            imm = 0
            if self.imm_gen:
                imm = self.imm_gen()

        # Special handling for certain instructions
        if self.name in ['ebreak', 'ecall']:
            # These have no registers or immediates
            rd = rs1 = rs2 = imm = 0
        elif self.format == InstructionFormat.R:
            # No immediate for R-type
            imm = 0
        elif self.format == InstructionFormat.U or self.format == InstructionFormat.J:
            # Only rd and immediate
            rs1 = rs2 = 0
        elif self.format == InstructionFormat.I:
            # Only rd, rs1, and immediate
            rs2 = 0
        elif self.format == InstructionFormat.S or self.format == InstructionFormat.B:
            # Only rs1, rs2, and immediate
            rd = 0

        encoded = self.encode(rd, rs1, rs2, imm)
        asm = self.assembly(rd, rs1, rs2, imm)
        return encoded, asm

    def assembly(self, rd: int, rs1: int, rs2: int, imm: int) -> str:
        """Generate assembly string for this instruction."""
        if self.name in ['ebreak', 'ecall']:
            return self.name

        reg_name = lambda r: f"x{r}"

        if self.format == InstructionFormat.R:
            return f"{self.name} {reg_name(rd)}, {reg_name(rs1)}, {reg_name(rs2)}"
        elif self.format == InstructionFormat.I:
            # Handle shift instructions with shamt
            if self.name in ['slli', 'srli', 'srai']:
                shamt = imm & 0x1f  # only lower 5 bits
                return f"{self.name} {reg_name(rd)}, {reg_name(rs1)}, {shamt}"
            # Handle load instructions (lb, lh, lw, lbu, lhu) and jalr
            elif self.name in ['lb', 'lh', 'lw', 'lbu', 'lhu', 'jalr']:
                return f"{self.name} {reg_name(rd)}, {imm}({reg_name(rs1)})"
            else:
                # Regular I-type: addi, xori, ori, andi, slti, sltiu
                return f"{self.name} {reg_name(rd)}, {reg_name(rs1)}, {imm}"
        elif self.format == InstructionFormat.S:
            return f"{self.name} {reg_name(rs2)}, {imm}({reg_name(rs1)})"
        elif self.format == InstructionFormat.B:
            return f"{self.name} {reg_name(rs1)}, {reg_name(rs2)}, {imm}"
        elif self.format == InstructionFormat.U:
            return f"{self.name} {reg_name(rd)}, {imm}"
        elif self.format == InstructionFormat.J:
            return f"{self.name} {reg_name(rd)}, {imm}"
        else:
            return f"{self.name} unknown_format"

    def __str__(self) -> str:
        return f"{self.name} ({self.format.value}-type)"


class RISCVISA:
    """RISC-V instruction set definition and generator."""

    def __init__(self, weights: Optional[Dict[str, float]] = None,
                 load_store_offset_min: int = -2048,
                 load_store_offset_max: int = 2047,
                 load_store_offset_ranges: Optional[List[Tuple[int, int]]] = None,
                 rd_min: int = 0, rd_max: int = 31,
                 rs1_min: int = 0, rs1_max: int = 31,
                 rs2_min: int = 0, rs2_max: int = 31):
        # Handle load/store offset ranges
        if load_store_offset_ranges is not None:
            # Validate ranges
            self.load_store_offset_ranges = []
            for base, size in load_store_offset_ranges:
                if size <= 0:
                    raise ValueError(f"Range size must be positive, got size={size} for base={base}")
                self.load_store_offset_ranges.append((base, size))
            # Compute overall min/max for backward compatibility
            all_offsets = [base for base, size in self.load_store_offset_ranges]
            self.load_store_offset_min = min(all_offsets)
            self.load_store_offset_max = max(base + size - 1 for base, size in self.load_store_offset_ranges)
        else:
            # Use single range from min/max
            if load_store_offset_min > load_store_offset_max:
                raise ValueError(f"load_store_offset_min ({load_store_offset_min}) > load_store_offset_max ({load_store_offset_max})")
            self.load_store_offset_min = load_store_offset_min
            self.load_store_offset_max = load_store_offset_max
            self.load_store_offset_ranges = [(load_store_offset_min, load_store_offset_max - load_store_offset_min + 1)]

        # Validate and store register ranges
        self._validate_register_range("rd", rd_min, rd_max)
        self._validate_register_range("rs1", rs1_min, rs1_max)
        self._validate_register_range("rs2", rs2_min, rs2_max)
        self.rd_min = rd_min
        self.rd_max = rd_max
        self.rs1_min = rs1_min
        self.rs1_max = rs1_max
        self.rs2_min = rs2_min
        self.rs2_max = rs2_max

        self.instructions: List[Instruction] = []
        self._load_instructions()

        # Initialize weights: default is 1.0 for all instructions
        self.weights: Dict[str, float] = {}
        for instr in self.instructions:
            self.weights[instr.name] = 1.0

        # Update with any provided weights
        if weights:
            for name, weight in weights.items():
                if name in self.weights:
                    self.weights[name] = weight
                else:
                    raise ValueError(f"Unknown instruction '{name}' in weights")

    def generate_load_store_offset(self) -> int:
        """Generate a random load/store offset from configured ranges."""
        # Randomly select a range
        base, size = random.choice(self.load_store_offset_ranges)
        # Generate offset within range [base, base + size - 1]
        return random.randint(base, base + size - 1)

    def _validate_register_range(self, reg_type: str, min_val: int, max_val: int):
        """Validate register range parameters."""
        if min_val < 0 or max_val > 31:
            raise ValueError(f"{reg_type} range [{min_val}, {max_val}] must be within 0-31.")
        if min_val > max_val:
            raise ValueError(f"{reg_type} min ({min_val}) > max ({max_val})")

    def get_random_rd(self, exclude_zero: bool = False) -> int:
        """Return a random destination register within configured rd range."""
        return Registers.random_range(self.rd_min, self.rd_max, exclude_zero=exclude_zero)

    def get_random_rs1(self, exclude_zero: bool = False) -> int:
        """Return a random source register 1 within configured rs1 range."""
        return Registers.random_range(self.rs1_min, self.rs1_max, exclude_zero=exclude_zero)

    def get_random_rs2(self, exclude_zero: bool = False) -> int:
        """Return a random source register 2 within configured rs2 range."""
        return Registers.random_range(self.rs2_min, self.rs2_max, exclude_zero=exclude_zero)

    def generate_random_instruction(self, instr: Optional[Instruction] = None) -> Tuple[int, str]:
        """Generate a random instruction using configured register ranges.

        Args:
            instr: Specific instruction to generate. If None, selects random instruction.

        Returns:
            (encoded_instruction, assembly_string)
        """
        if instr is None:
            instr = self.get_random_instruction()

        # Generate registers using configured ranges
        rd = self.get_random_rd()
        rs1 = self.get_random_rs1()
        rs2 = self.get_random_rs2()

        # Let instruction generate with these registers (it will handle format-specific zeroing)
        return instr.generate_with_registers(rd=rd, rs1=rs1, rs2=rs2, imm=None)

    def _load_instructions(self):
        """Load common RV32I instructions."""
        # R-type instructions
        self.instructions.extend([
            Instruction("add", InstructionFormat.R, 0b0110011, 0b000, 0b0000000),
            Instruction("sub", InstructionFormat.R, 0b0110011, 0b000, 0b0100000),
            Instruction("xor", InstructionFormat.R, 0b0110011, 0b100, 0b0000000),
            Instruction("or", InstructionFormat.R, 0b0110011, 0b110, 0b0000000),
            Instruction("and", InstructionFormat.R, 0b0110011, 0b111, 0b0000000),
            Instruction("sll", InstructionFormat.R, 0b0110011, 0b001, 0b0000000),
            Instruction("srl", InstructionFormat.R, 0b0110011, 0b101, 0b0000000),
            Instruction("sra", InstructionFormat.R, 0b0110011, 0b101, 0b0100000),
            Instruction("slt", InstructionFormat.R, 0b0110011, 0b010, 0b0000000),
            Instruction("sltu", InstructionFormat.R, 0b0110011, 0b011, 0b0000000),
        ])

        # I-type instructions (with immediates)
        def imm_12bit(): return random.randint(-2048, 2047)
        def imm_5bit(): return random.randint(0, 31)
        imm_load_store = self.generate_load_store_offset

        self.instructions.extend([
            Instruction("addi", InstructionFormat.I, 0b0010011, 0b000, imm_gen=imm_12bit),
            Instruction("xori", InstructionFormat.I, 0b0010011, 0b100, imm_gen=imm_12bit),
            Instruction("ori", InstructionFormat.I, 0b0010011, 0b110, imm_gen=imm_12bit),
            Instruction("andi", InstructionFormat.I, 0b0010011, 0b111, imm_gen=imm_12bit),
            Instruction("slli", InstructionFormat.I, 0b0010011, 0b001, imm_gen=imm_5bit),
            Instruction("srli", InstructionFormat.I, 0b0010011, 0b101, 0b0000000, imm_gen=imm_5bit),
            Instruction("srai", InstructionFormat.I, 0b0010011, 0b101, 0b0100000, imm_gen=imm_5bit),
            Instruction("slti", InstructionFormat.I, 0b0010011, 0b010, imm_gen=imm_12bit),
            Instruction("sltiu", InstructionFormat.I, 0b0010011, 0b011, imm_gen=imm_12bit),
            Instruction("lb", InstructionFormat.I, 0b0000011, 0b000, imm_gen=imm_load_store),
            Instruction("lh", InstructionFormat.I, 0b0000011, 0b001, imm_gen=imm_load_store),
            Instruction("lw", InstructionFormat.I, 0b0000011, 0b010, imm_gen=imm_load_store),
            Instruction("lbu", InstructionFormat.I, 0b0000011, 0b100, imm_gen=imm_load_store),
            Instruction("lhu", InstructionFormat.I, 0b0000011, 0b101, imm_gen=imm_load_store),
            Instruction("jalr", InstructionFormat.I, 0b1100111, 0b000, imm_gen=imm_12bit),
        ])

        # S-type instructions
        self.instructions.extend([
            Instruction("sb", InstructionFormat.S, 0b0100011, 0b000, imm_gen=imm_load_store),
            Instruction("sh", InstructionFormat.S, 0b0100011, 0b001, imm_gen=imm_load_store),
            Instruction("sw", InstructionFormat.S, 0b0100011, 0b010, imm_gen=imm_load_store),
        ])

        # B-type instructions
        def imm_branch(): return random.randint(-4096, 4094) & ~1  # align to 2 bytes
        self.instructions.extend([
            Instruction("beq", InstructionFormat.B, 0b1100011, 0b000, imm_gen=imm_branch),
            Instruction("bne", InstructionFormat.B, 0b1100011, 0b001, imm_gen=imm_branch),
            Instruction("blt", InstructionFormat.B, 0b1100011, 0b100, imm_gen=imm_branch),
            Instruction("bge", InstructionFormat.B, 0b1100011, 0b101, imm_gen=imm_branch),
            Instruction("bltu", InstructionFormat.B, 0b1100011, 0b110, imm_gen=imm_branch),
            Instruction("bgeu", InstructionFormat.B, 0b1100011, 0b111, imm_gen=imm_branch),
        ])

        # U-type instructions
        def imm_20bit(): return random.randint(-524288, 524287)  # 20-bit signed
        self.instructions.extend([
            Instruction("lui", InstructionFormat.U, 0b0110111, imm_gen=imm_20bit),
            Instruction("auipc", InstructionFormat.U, 0b0010111, imm_gen=imm_20bit),
        ])

        # J-type instructions
        def imm_jump(): return random.randint(-1048576, 1048574) & ~1  # align to 2 bytes
        self.instructions.extend([
            Instruction("jal", InstructionFormat.J, 0b1101111, imm_gen=imm_jump),
        ])

        # Special instructions
        self.instructions.extend([
            Instruction("ecall", InstructionFormat.I, 0b1110011, 0b000),
            Instruction("ebreak", InstructionFormat.I, 0b1110011, 0b000, 0b0000001),
        ])

    def get_random_instruction(self) -> Instruction:
        """Return a random instruction from the ISA using weighted selection."""
        # Get weights for all instructions in order
        weights = [self.weights[instr.name] for instr in self.instructions]
        return random.choices(self.instructions, weights=weights, k=1)[0]

    def get_weighted_random_from_list(self, instruction_list: List[Instruction]) -> Instruction:
        """Return a random instruction from a subset using weighted selection."""
        if not instruction_list:
            raise ValueError("Instruction list cannot be empty")
        # Get weights for the provided instructions
        weights = [self.weights[instr.name] for instr in instruction_list]
        return random.choices(instruction_list, weights=weights, k=1)[0]

    def set_weight_by_name(self, name: str, weight: float):
        """Set weight for a specific instruction by name."""
        if name not in self.weights:
            raise ValueError(f"Unknown instruction '{name}'")
        if weight < 0:
            raise ValueError(f"Weight must be non-negative, got {weight}")
        self.weights[name] = weight

    def set_weight_by_format(self, fmt: InstructionFormat, weight: float):
        """Set weight for all instructions of a given format."""
        if weight < 0:
            raise ValueError(f"Weight must be non-negative, got {weight}")
        for instr in self.instructions:
            if instr.format == fmt:
                self.weights[instr.name] = weight

    def get_weight(self, name: str) -> float:
        """Get weight for a specific instruction."""
        if name not in self.weights:
            raise ValueError(f"Unknown instruction '{name}'")
        return self.weights[name]

    def generate_random(self, count: int = 1) -> List[Tuple[int, str]]:
        """Generate `count` random instructions.
        Returns list of (encoded, assembly)."""
        results = []
        for _ in range(count):
            instr = self.get_random_instruction()
            encoded, asm = self.generate_random_instruction(instr)
            results.append((encoded, asm))
        return results

    def get_instructions_by_format(self, fmt: InstructionFormat) -> List[Instruction]:
        """Get all instructions of a given format."""
        return [instr for instr in self.instructions if instr.format == fmt]

    def __str__(self) -> str:
        return f"RISCVISA with {len(self.instructions)} instructions"


# Utility functions
def format_binary(word: int, bits: int = 32) -> str:
    """Format integer as binary string with given bits."""
    return format(word, f'0{bits}b')

def format_hex(word: int, bits: int = 32) -> str:
    """Format integer as hex string with given bits."""
    return format(word, f'0{bits//4}x')

def disassemble(word: int) -> Optional[str]:
    """Simple disassembler (placeholder)."""
    # This would require a proper disassembler implementation
    # For now, just return hex representation
    return f"0x{word:08x}"