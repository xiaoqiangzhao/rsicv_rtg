#!/bin/bash
# Skill: List available RISC-V instructions
# Usage: skill-list [--detailed]

if [[ "$1" == "--detailed" ]]; then
    echo "Listing all available RISC-V instructions with details:"
    python3 -m generator --list-instructions
else
    echo "Available RISC-V instructions:"
    python3 -m generator --list-instructions | grep -E "^  [a-z]" | awk '{print $1}' | sort | tr '\n' ' '
    echo ""
fi