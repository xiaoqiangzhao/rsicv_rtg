#!/usr/bin/env python3
"""
Unit tests for configuration file support.
"""

import unittest
import tempfile
import os
import argparse
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from riscv_rtg.generator.cli import load_config, validate_and_convert_config, merge_config_with_args


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading functions."""

    def test_load_config_valid(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('count: 10\nformat: "asm"\nseed: 42\n')
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertEqual(config['count'], 10)
            self.assertEqual(config['format'], 'asm')
            self.assertEqual(config['seed'], 42)
        finally:
            os.unlink(config_path)

    def test_load_config_missing_file(self):
        """Test loading missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_config('/nonexistent/path/config.yaml')

    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('count: 10\ninvalid yaml\n')
            config_path = f.name

        try:
            with self.assertRaises(ValueError):
                load_config(config_path)
        finally:
            os.unlink(config_path)

    def test_validate_and_convert_config(self):
        """Test type conversion and validation."""
        raw = {
            'count': '10',  # string
            'base_address': '0x1000',  # hex string
            'pattern_density': '0.5',  # string float
            'weights': {'r': '2.0', 'i': '0.5'}  # nested dict
        }
        validated = validate_and_convert_config(raw)

        self.assertEqual(validated['count'], 10)
        self.assertEqual(validated['base_address'], 0x1000)
        self.assertEqual(validated['pattern_density'], 0.5)
        self.assertEqual(validated['weights']['r'], 2.0)
        self.assertEqual(validated['weights']['i'], 0.5)

    def test_validate_and_convert_config_empty(self):
        """Test empty config returns empty dict."""
        self.assertEqual(validate_and_convert_config({}), {})
        self.assertEqual(validate_and_convert_config(None), {})

    def test_merge_config_with_args_weights(self):
        """Test merging weights from config with CLI args."""
        config = {'weights': {'r': 2.0, 'i': 0.5}}

        # Simulate CLI args with default weights (1.0)
        args = argparse.Namespace(weight_r=1.0, weight_i=1.0, weight_s=1.0,
                                  weight_b=1.0, weight_u=1.0, weight_j=1.0,
                                  weight_special=1.0)

        merged = merge_config_with_args(config, args)
        # Config weights should apply since CLI used defaults
        self.assertEqual(merged.weight_r, 2.0)
        self.assertEqual(merged.weight_i, 0.5)
        self.assertEqual(merged.weight_s, 1.0)  # unchanged

        # Test CLI override
        args2 = argparse.Namespace(weight_r=3.0, weight_i=1.0)
        merged2 = merge_config_with_args(config, args2)
        self.assertEqual(merged2.weight_r, 3.0)  # CLI overrides
        self.assertEqual(merged2.weight_i, 1.0)  # CLI overrides (default 1.0, but CLI set 1.0, cannot distinguish)

    def test_merge_config_with_args_other_fields(self):
        """Test merging other fields from config."""
        config = {'count': 50, 'format': 'asm', 'seed': 123}

        # CLI with default values (should be overridden by config)
        args = argparse.Namespace(count=10, format='hex', seed=None)
        defaults = {'count': 10, 'format': 'hex', 'seed': None}
        merged = merge_config_with_args(config, args, defaults)
        self.assertEqual(merged.count, 50)  # config overrides default
        self.assertEqual(merged.format, 'asm')  # config overrides default
        self.assertEqual(merged.seed, 123)  # config overrides None

        # CLI with explicit values (should override config)
        args2 = argparse.Namespace(count=5, format='bin', seed=999)
        merged2 = merge_config_with_args(config, args2, defaults)
        self.assertEqual(merged2.count, 5)  # CLI overrides
        self.assertEqual(merged2.format, 'bin')  # CLI overrides
        self.assertEqual(merged2.seed, 999)  # CLI overrides

    def test_merge_config_with_args_store_true(self):
        """Test merging store_true flags."""
        config = {'pc_comments': True, 'list_instructions': False}

        # CLI defaults (False)
        args = argparse.Namespace(pc_comments=False, list_instructions=False)
        defaults = {'pc_comments': False, 'list_instructions': False}
        merged = merge_config_with_args(config, args, defaults)
        self.assertEqual(merged.pc_comments, True)  # config overrides default
        self.assertEqual(merged.list_instructions, False)  # config same as default

        # CLI explicitly set (should override config)
        args2 = argparse.Namespace(pc_comments=True, list_instructions=True)
        merged2 = merge_config_with_args(config, args2, defaults)
        self.assertEqual(merged2.pc_comments, True)  # CLI overrides (same as config)
        self.assertEqual(merged2.list_instructions, True)  # CLI overrides


if __name__ == '__main__':
    unittest.main()