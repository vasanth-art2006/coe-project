import json
import os
import random
import numpy as np
from datetime import datetime, timedelta

def load_schema_rules():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_rules.json')
    with open(path, 'r') as f:
        return json.load(f)

def load_distributions():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'distributions.json')
    with open(path, 'r') as f:
        return json.load(f)

def generate_transactions(accounts, devices, n_transactions):
    rules = load_schema_rules()['transaction']
    dist = load_distributions()
    
    t_types = list(dist['transaction_types'].keys())
    t_probs = list(dist['transaction_types'].values())
    
    s_types = list(dist['transaction_status'].keys())
    s_probs = list(dist['transaction_status'].values())
    
    transactions = []
    
    for i in range(1, n_transactions + 1):
        account = random.choice(accounts)
        
        # Match device to customer to maintain referential logic if possible, 
        # or just pick a random device for simplicity in the baseline.
        # Let's try to find a device owned by the account's customer
        customer_devices = [d for d in devices if d['customer_id'] == account['customer_id']]
        if not customer_devices:
            device = random.choice(devices)
        else:
            device = random.choice(customer_devices)
            
        t_type = np.random.choice(t_types, p=t_probs)
        t_status = np.random.choice(s_types, p=s_probs)
        
        date_obj = datetime.now() - timedelta(days=random.randint(0, 365))
        
        transaction = {
            'transaction_id': f"T{str(i).zfill(7)}",
            'account_id': account['account_id'],
            'device_id': device['device_id'],
            'transaction_type': t_type,
            'amount': round(random.uniform(rules['amount']['min'], min(account['balance'] + 1000, rules['amount']['max'])), 2),
            'transaction_status': t_status,
            'transaction_date': date_obj.strftime("%Y-%m-%d %H:%M:%S"),
            'beneficiary_type': 'INTERNAL',
            'failure_reason': 'NONE' if t_status == 'SUCCESS' else 'UNKNOWN'
        }
        transactions.append(transaction)
        
    return transactions
