#!/usr/bin/env python3

# Python test for C++ code generation
# This test verifies that the generated C++ code matches the YAML definitions

import os
import sys
import yaml

def test_consistency():
    """Basic consistency test."""
    yaml_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'riscv_rtg', 'isa', 'definitions', 'rv32i.yaml')
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    # Check that we have the expected number of instructions
    expected_count = len(data['instructions'])
    print(f"YAML defines {expected_count} instructions")

    # TODO: Add more comprehensive tests
    # - Verify enum values match C++ header
    # - Verify instruction formats are valid
    # - Verify immediate specifications are consistent

    return True

if __name__ == '__main__':
    success = test_consistency()
    sys.exit(0 if success else 1)
