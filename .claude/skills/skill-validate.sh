#!/bin/bash
# Skill: Validate configuration file
# Usage: skill-validate [config.yaml]

CONFIG_FILE="${1:-example_config.yaml}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    echo "Available config files:"
    ls -la *.yaml *.yml 2>/dev/null || echo "No YAML files found"
    exit 1
fi

echo "Validating configuration file: $CONFIG_FILE"
echo ""

# Try to load the config with Python
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from generator import load_config, validate_and_convert_config
    config = load_config('$CONFIG_FILE')
    validated = validate_and_convert_config(config)
    print('✓ Configuration file is valid')
    print('')
    print('Loaded configuration:')
    for key, value in validated.items():
        if key == 'weights' and isinstance(value, dict):
            print(f'  {key}:')
            for k, v in value.items():
                print(f'    {k}: {v}')
        else:
            print(f'  {key}: {value}')
except Exception as e:
    print(f'✗ Error in configuration: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "To test this configuration:"
    echo "  python3 -m generator --config $CONFIG_FILE -n 5 -f asm"
fi