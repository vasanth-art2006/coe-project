import json
import os

def load_device_rules():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'device_rules.json')
    with open(path, 'r') as f:
        return json.load(f)

def validate_device_os(device_type, os_version):
    rules = load_device_rules().get('device_os_mapping', {})
    if device_type not in rules:
        return False, [f"Unknown device type {device_type}"]
        
    valid_os = rules[device_type]
    if os_version not in valid_os:
        return False, [f"Invalid OS {os_version} for device {device_type}"]
        
    return True, []
