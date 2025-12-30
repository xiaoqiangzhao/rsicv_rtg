#!/bin/bash
# Skill: Run tests for riscv_rtg
# Usage: This script runs the test suite

echo "Running tests for riscv_rtg..."
python3 -m pytest tests/ -xvs "$@"