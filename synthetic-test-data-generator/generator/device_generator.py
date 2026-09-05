import json
import os
import random
import numpy as np

def load_device_rules():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'device_rules.json')
    with open(path, 'r') as f:
        return json.load(f)

def load_distributions():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'distributions.json')
    with open(path, 'r') as f:
        return json.load(f)

def generate_devices(customers, n_devices=None):
    rules = load_device_rules()
    dist = load_distributions()['device_distribution']
    
    device_types = list(dist.keys())
    probs = list(dist.values())
    
    devices = []
    if n_devices is None:
        n_devices = len(customers)
        
    for i in range(1, n_devices + 1):
        customer = random.choice(customers)
        device_type = np.random.choice(device_types, p=probs)
        os_version = random.choice(rules['device_os_mapping'][device_type])
        
        device = {
            'device_id': f"D{str(i).zfill(5)}",
            'customer_id': customer['customer_id'],
            'device_type': device_type,
            'manufacturer': 'Synthetic',
            'model': f"Model-{random.randint(1, 10)}",
            'os': os_version.split(' ')[0],
            'os_version': os_version.split(' ')[1] if ' ' in os_version else os_version,
            'app_version': f"{random.randint(1, 5)}.{random.randint(0, 9)}",
            'device_status': 'ACTIVE'
        }
        devices.append(device)
        
    return devices
