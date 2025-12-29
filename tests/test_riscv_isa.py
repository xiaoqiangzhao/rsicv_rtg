#!/usr/bin/env python3
"""
Unit tests for RISC-V ISA generator.
"""

import unittest
import random
from riscv_isa import RISCVISA, InstructionFormat, Registers, format_binary, format_hex


class TestRISCVISA(unittest.TestCase):
    """Test RISCVISA class."""

    def setUp(self):
        self.isa = RISCVISA()

    def test_instruction_count(self):
        """Test that instructions are loaded."""
        self.assertGreater(len(self.isa.instructions), 0)
        print(f"Loaded {len(self.isa.instructions)} instructions")

    def test_get_random_instruction(self):
        """Test get_random_instruction returns an instruction."""
        instr = self.isa.get_random_instruction()
        self.assertIsNotNone(instr)
        self.assertIsNotNone(instr.name)
        self.assertIsInstance(instr.format, InstructionFormat)

    def test_generate_random(self):
        """Test generate_random returns correct number of instructions."""
        results = self.isa.generate_random(5)
        self.assertEqual(len(results), 5)
        for encoded, asm in results:
            self.assertIsInstance(encoded, int)
            self.assertIsInstance(asm, str)
            # Check encoded is 32-bit
            self.assertTrue(0 <= encoded < (1 << 32))

    def test_instruction_formats(self):
        """Test instruction format categorization."""
        for fmt in InstructionFormat:
            instructions = self.isa.get_instructions_by_format(fmt)
            if instructions:
                print(f"Format {fmt.value}: {len(instructions)} instructions")
                for instr in instructions[:3]:
                    self.assertEqual(instr.format, fmt)

    def test_register_enum(self):
        """Test register enumeration."""
        self.assertEqual(Registers.ZERO.value, 0)
        self.assertEqual(Registers.RA.value, 1)
        self.assertEqual(Registers.T6.value, 31)

    def test_register_random(self):
        """Test random register generation."""
        for _ in range(10):
            reg = Registers.random()
            self.assertTrue(0 <= reg <= 31)
            reg_no_zero = Registers.random(exclude_zero=True)
            self.assertTrue(1 <= reg_no_zero <= 31)

    def test_format_functions(self):
        """Test binary and hex formatting."""
        word = 0x12345678
        self.assertEqual(format_binary(word), format(word, '032b'))
        self.assertEqual(format_hex(word), format(word, '08x'))

    def test_reproducible_generation(self):
        """Test that seed produces same results."""
        random.seed(42)
        results1 = self.isa.generate_random(5)
        random.seed(42)
        results2 = self.isa.generate_random(5)
        self.assertEqual(results1, results2)

    def test_instruction_encoding(self):
        """Test that encoding produces valid 32-bit words."""
        # Test a few specific instructions
        for instr in self.isa.instructions[:10]:  # Sample first 10
            encoded, asm = instr.generate_random()
            self.assertTrue(0 <= encoded < (1 << 32))
            # Check that opcode is in lower 7 bits
            self.assertEqual(encoded & 0x7f, instr.opcode)

    def test_weight_initialization(self):
        """Test that weights are initialized correctly."""
        # Default weights should be 1.0 for all instructions
        for instr in self.isa.instructions:
            self.assertEqual(self.isa.get_weight(instr.name), 1.0)

    def test_weight_by_name(self):
        """Test setting weight by instruction name."""
        self.isa.set_weight_by_name("add", 2.5)
        self.assertEqual(self.isa.get_weight("add"), 2.5)
        # Other instructions should still be 1.0
        self.assertEqual(self.isa.get_weight("sub"), 1.0)

        # Test error for unknown instruction
        with self.assertRaises(ValueError):
            self.isa.set_weight_by_name("unknown_instr", 1.0)

        # Test error for negative weight
        with self.assertRaises(ValueError):
            self.isa.set_weight_by_name("add", -1.0)

    def test_weight_by_format(self):
        """Test setting weight by instruction format."""
        # Set weight for R-type instructions
        self.isa.set_weight_by_format(InstructionFormat.R, 3.0)
        for instr in self.isa.instructions:
            if instr.format == InstructionFormat.R:
                self.assertEqual(self.isa.get_weight(instr.name), 3.0)
            else:
                self.assertEqual(self.isa.get_weight(instr.name), 1.0)

    def test_weighted_selection(self):
        """Test that weighted selection respects weights."""
        # Set weight for "add" to 0, others to 1
        self.isa.set_weight_by_name("add", 0.0)

        # Generate many instructions, "add" should never appear
        for _ in range(100):
            instr = self.isa.get_random_instruction()
            self.assertNotEqual(instr.name, "add")

    def test_weighted_selection_high_weight(self):
        """Test that high weight increases frequency."""
        # Count occurrences of "add" with normal weight
        random.seed(42)
        normal_count = 0
        for _ in range(100):
            instr = self.isa.get_random_instruction()
            if instr.name == "add":
                normal_count += 1

        # Reset weights and set "add" weight to 10
        self.isa.set_weight_by_name("add", 10.0)
        random.seed(42)
        high_weight_count = 0
        for _ in range(100):
            instr = self.isa.get_random_instruction()
            if instr.name == "add":
                high_weight_count += 1

        # With weight 10, "add" should appear more often
        self.assertGreater(high_weight_count, normal_count)

    def test_get_weighted_random_from_list(self):
        """Test weighted selection from a subset."""
        # Get only R-type instructions
        r_type = self.isa.get_instructions_by_format(InstructionFormat.R)
        # Set weight for "add" to 0 within R-type
        self.isa.set_weight_by_name("add", 0.0)

        # Generate many instructions from R-type subset
        for _ in range(50):
            instr = self.isa.get_weighted_random_from_list(r_type)
            self.assertIn(instr, r_type)
            self.assertNotEqual(instr.name, "add")


class TestInstructionFormats(unittest.TestCase):
    """Test instruction format encoding."""

    def test_r_type_encoding(self):
        """Test R-type encoding."""
        from riscv_isa import Instruction
        instr = Instruction("add", InstructionFormat.R, 0b0110011, 0b000, 0b0000000)
        # add x1, x2, x3
        encoded = instr.encode(rd=1, rs1=2, rs2=3, imm=0)
        # Expected: funct7=0, rs2=3, rs1=2, funct3=0, rd=1, opcode=0110011
        expected = (0b0000000 << 25) | (3 << 20) | (2 << 15) | (0b000 << 12) | (1 << 7) | 0b0110011
        self.assertEqual(encoded, expected)

    def test_i_type_encoding(self):
        """Test I-type encoding."""
        from riscv_isa import Instruction
        instr = Instruction("addi", InstructionFormat.I, 0b0010011, 0b000)
        # addi x1, x2, 0x123
        encoded = instr.encode(rd=1, rs1=2, rs2=0, imm=0x123)
        # Expected: imm=0x123, rs1=2, funct3=0, rd=1, opcode=0010011
        expected = (0x123 << 20) | (2 << 15) | (0b000 << 12) | (1 << 7) | 0b0010011
        self.assertEqual(encoded, expected)

    def test_s_type_encoding(self):
        """Test S-type encoding."""
        from riscv_isa import Instruction
        instr = Instruction("sw", InstructionFormat.S, 0b0100011, 0b010)
        # sw x3, 0x44(x2)
        encoded = instr.encode(rd=0, rs1=2, rs2=3, imm=0x44)
        # imm[11:5]=0x02, imm[4:0]=0x04
        # 0x44 = 0b000001000100
        # imm[11:5]=0000010, imm[4:0]=00100
        expected = (0b0000010 << 25) | (3 << 20) | (2 << 15) | (0b010 << 12) | (0b00100 << 7) | 0b0100011
        self.assertEqual(encoded, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)