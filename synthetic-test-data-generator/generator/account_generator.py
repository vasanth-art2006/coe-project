import json
import os
import random

def load_schema_rules():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_rules.json')
    with open(path, 'r') as f:
        return json.load(f)

def generate_accounts(customers, n_accounts=None):
    rules = load_schema_rules()['account']
    accounts = []
    
    if n_accounts is None:
        n_accounts = len(customers)
        
    for i in range(1, n_accounts + 1):
        customer = random.choice(customers)
        account = {
            'account_id': f"A{str(i).zfill(5)}",
            'customer_id': customer['customer_id'],
            'account_type': random.choice(rules['types']),
            'balance': round(random.uniform(rules['balance']['min'], rules['balance']['max']), 2),
            'currency': 'INR',
            'account_status': random.choice(rules['status'])
        }
        accounts.append(account)
        
    return accounts
