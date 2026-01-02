#!/usr/bin/env python3
"""
RISC-V ISA enums matching C++ header riscv_isa.h.
Generated from definitions/rv32i.yaml.
"""

from enum import Enum, IntEnum


class RiscvOpcode(IntEnum):
    """RISC-V instruction opcodes matching C++ RiscvOpcode enum."""
    LOAD      = 0b0000011
    STORE     = 0b0100011
    OP_IMM    = 0b0010011
    OP        = 0b0110011
    BRANCH    = 0b1100011
    JAL       = 0b1101111
    JALR      = 0b1100111
    SYSTEM    = 0b1110011
    LUI       = 0b0110111
    AUIPC     = 0b0010111
    FENCE     = 0b0001111
    CUSTOM    = 0b0001011


class RiscvFunct3(IntEnum):
    """RISC-V instruction funct3 values matching C++ RiscvFunct3 enum."""
    # Load
    LB        = 0b000
    LH        = 0b001
    LW        = 0b010
    LBU       = 0b100
    LHU       = 0b101
    # Store
    SB        = 0b000
    SH        = 0b001
    SW        = 0b010
    # OP-IMM
    ADDI      = 0b000
    SLTI      = 0b010
    SLTIU     = 0b011
    XORI      = 0b100
    ORI       = 0b110
    ANDI      = 0b111
    SLLI      = 0b001
    SRLI_SRAI = 0b101
    # OP
    ADD_SUB   = 0b000
    SLL       = 0b001
    SLT       = 0b010
    SLTU      = 0b011
    XOR       = 0b100
    SRL_SRA   = 0b101
    OR        = 0b110
    AND       = 0b111
    # Multiply/Divide extension (same funct3 values, different funct7)
    MUL        = 0b000
    MULH       = 0b001
    MULHSU     = 0b010
    MULHU      = 0b011
    DIV        = 0b100
    DIVU       = 0b101
    REM        = 0b110
    REMU       = 0b111
    # Branch
    BEQ       = 0b000
    BNE       = 0b001
    BLT       = 0b100
    BGE       = 0b101
    BLTU      = 0b110
    BGEU      = 0b111
    # System
    ECALL_EBREAK = 0b000
    CSRRW     = 0b001
    CSRRS     = 0b010
    CSRRC     = 0b011
    CSRRWI    = 0b101
    CSRRSI    = 0b110
    CSRRCI    = 0b111
    # Fence
    FENCE     = 0b000
    FENCE_I   = 0b001


class RiscvFunct7(IntEnum):
    """RISC-V instruction funct7 values matching C++ RiscvFunct7 enum."""
    BASE = 0b0000000
    ALT  = 0b0100000
    MULDIV = 0b0000001


class RiscvInstructionType(Enum):
    """RISC-V instruction types matching C++ RiscvInstructionType enum."""
    R_TYPE = "R_TYPE"
    I_TYPE = "I_TYPE"
    S_TYPE = "S_TYPE"
    B_TYPE = "B_TYPE"
    U_TYPE = "U_TYPE"
    J_TYPE = "J_TYPE"
    UNKNOWN = "UNKNOWN"


# Mapping from InstructionFormat (existing) to RiscvInstructionType
INSTRUCTION_FORMAT_TO_TYPE = {
    'R': RiscvInstructionType.R_TYPE,
    'I': RiscvInstructionType.I_TYPE,
    'S': RiscvInstructionType.S_TYPE,
    'B': RiscvInstructionType.B_TYPE,
    'U': RiscvInstructionType.U_TYPE,
    'J': RiscvInstructionType.J_TYPE,
}