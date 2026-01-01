#!/usr/bin/env python3
"""
Unit tests for semantic correlation features.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from riscv_rtg.generator.patterns import SemanticState, CommentGenerator, PatternGenerator
from riscv_rtg.isa.riscv_isa import RISCVISA, InstructionFormat, Registers


class TestSemanticState(unittest.TestCase):
    """Test SemanticState class."""

    def test_initial_state(self):
        """Test initial semantic state is empty."""
        state = SemanticState()
        self.assertEqual(state.register_writers, {})
        self.assertEqual(state.register_readers, {})
        self.assertEqual(state.memory_accesses, {})
        self.assertEqual(state.loop_nesting, 0)
        self.assertIsNone(state.current_loop_counter_reg)
        self.assertEqual(state.branch_targets, {})
        self.assertFalse(state.in_function)
        self.assertEqual(state.stack_pointer_offset, 0)
        self.assertEqual(state.saved_registers, [])

    def test_register_write(self):
        """Test updating register write."""
        state = SemanticState()
        state.update_register_write(5, 10)
        self.assertEqual(state.register_writers[5], 10)
        self.assertEqual(state.register_readers.get(5), [])

    def test_register_read(self):
        """Test updating register read."""
        state = SemanticState()
        state.update_register_read(7, 3)
        self.assertEqual(state.register_readers[7], [3])
        state.update_register_read(7, 5)
        self.assertEqual(state.register_readers[7], [3, 5])

    def test_memory_access(self):
        """Test updating memory access."""
        state = SemanticState()
        state.update_memory_access(10, -4, 2)
        self.assertEqual(state.memory_accesses[10], [(-4, 2)])
        state.update_memory_access(10, 8, 3)
        self.assertEqual(state.memory_accesses[10], [(-4, 2), (8, 3)])

    def test_loop_enter_exit(self):
        """Test loop nesting."""
        state = SemanticState()
        state.enter_loop(5)
        self.assertEqual(state.loop_nesting, 1)
        self.assertEqual(state.current_loop_counter_reg, 5)
        state.enter_loop(7)
        self.assertEqual(state.loop_nesting, 2)
        self.assertEqual(state.current_loop_counter_reg, 7)
        state.exit_loop()
        self.assertEqual(state.loop_nesting, 1)
        self.assertEqual(state.current_loop_counter_reg, 7)  # Still innermost loop counter
        state.exit_loop()
        self.assertEqual(state.loop_nesting, 0)
        self.assertIsNone(state.current_loop_counter_reg)
        state.exit_loop()  # should not go negative
        self.assertEqual(state.loop_nesting, 0)

    def test_function_enter_exit(self):
        """Test function state."""
        state = SemanticState()
        state.enter_function()
        self.assertTrue(state.in_function)
        self.assertEqual(state.stack_pointer_offset, 0)
        self.assertEqual(state.saved_registers, [])
        state.allocate_stack(16)
        self.assertEqual(state.stack_pointer_offset, 16)
        state.save_register(5)
        self.assertEqual(state.saved_registers, [5])
        state.exit_function()
        self.assertFalse(state.in_function)
        self.assertEqual(state.stack_pointer_offset, 0)
        self.assertEqual(state.saved_registers, [])


class TestCommentGenerator(unittest.TestCase):
    """Test CommentGenerator class."""

    def setUp(self):
        self.state = SemanticState()
        self.isa = RISCVISA()

    def test_detail_levels(self):
        """Test comment generation with different detail levels."""
        # Minimal detail
        gen = CommentGenerator(self.state, "minimal")
        # Should not crash
        comment = gen.generate(self.isa.instructions[0], 1, 2, 3, 0, 0)
        # Could be None or string depending on instruction
        # Just ensure no exception

        # Medium detail
        gen = CommentGenerator(self.state, "medium")
        comment = gen.generate(self.isa.instructions[0], 1, 2, 3, 0, 0)

        # Detailed detail
        gen = CommentGenerator(self.state, "detailed")
        comment = gen.generate(self.isa.instructions[0], 1, 2, 3, 0, 0)

        # None detail
        gen = CommentGenerator(self.state, "none")
        comment = gen.generate(self.isa.instructions[0], 1, 2, 3, 0, 0)
        self.assertIsNone(comment)

    def test_no_semantic_state(self):
        """Test comment generator without semantic state."""
        gen = CommentGenerator(None, "medium")
        comment = gen.generate(self.isa.instructions[0], 1, 2, 3, 0, 0)
        self.assertIsNone(comment)


class TestPatternGeneratorSemantic(unittest.TestCase):
    """Test PatternGenerator with semantic features."""

    def setUp(self):
        self.isa = RISCVISA()

    def test_semantic_state_integration(self):
        """Test that pattern generator updates semantic state."""
        state = SemanticState()
        pattern_gen = PatternGenerator(self.isa, semantic_state=state)

        # Generate a load-store pair
        results = pattern_gen.generate_load_store_pair()
        self.assertEqual(len(results), 2)
        # Check that semantic state was updated (at least instruction index increased)
        # The exact updates depend on generated registers
        self.assertEqual(pattern_gen.instr_idx, 2)

    def test_comment_generation(self):
        """Test that comments are generated when enabled."""
        state = SemanticState()
        pattern_gen = PatternGenerator(self.isa, semantic_state=state, comment_detail="medium")

        # Generate a single random instruction
        encoded, asm = pattern_gen._generate_single_random_instruction()
        # Check if comment is present (may or may not be depending on instruction)
        # Just ensure no exception

    def test_no_semantic_state(self):
        """Test pattern generator without semantic state (backward compatibility)."""
        pattern_gen = PatternGenerator(self.isa)
        # Should work without errors
        results = pattern_gen.generate_random_sequence(5)
        self.assertEqual(len(results), 5)


if __name__ == '__main__':
    unittest.main()