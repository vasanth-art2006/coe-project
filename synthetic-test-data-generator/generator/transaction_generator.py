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

def generate_transactions(accounts, devices, n_transactions, distribution_model: str = "pareto", seed: int = None):
    """
    Generate synthetic transactions with specified statistical distribution model.
    Optimized for high-performance generation (10,000+ records in < 1s).
    
    Args:
        accounts: List of account dictionaries.
        devices: List of device dictionaries.
        n_transactions: Number of transactions to generate.
        distribution_model: 'pareto', 'lognormal', 'gaussian', or 'uniform'.
        seed: Random seed for reproducibility.
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    rules = load_schema_rules()['transaction']
    dist = load_distributions()
    
    t_types = list(dist['transaction_types'].keys())
    t_probs = list(dist['transaction_types'].values())
    
    s_types = list(dist['transaction_status'].keys())
    s_probs = list(dist['transaction_status'].values())
    
    # Pre-index devices by customer_id for O(1) instantaneous lookup
    devices_by_customer = {}
    for d in devices:
        cid = d.get('customer_id')
        if cid not in devices_by_customer:
            devices_by_customer[cid] = []
        devices_by_customer[cid].append(d)

    # Vectorized / batch sampling of categories
    sampled_t_types = np.random.choice(t_types, size=n_transactions, p=t_probs)
    sampled_s_types = np.random.choice(s_types, size=n_transactions, p=s_probs)
    
    # Pre-sample amounts using requested distribution
    model_cfg = dist.get('amount_distributions', {}).get(distribution_model, {})
    r_min = float(rules['amount']['min'])
    r_max = float(rules['amount']['max'])

    if distribution_model == 'pareto':
        alpha = float(model_cfg.get('alpha', 1.8))
        x_m = float(model_cfg.get('x_m', 10.0))
        raw_amounts = (np.random.pareto(alpha, size=n_transactions) + 1.0) * x_m
    elif distribution_model == 'lognormal':
        mean = float(model_cfg.get('mean', 6.2))
        sigma = float(model_cfg.get('sigma', 1.35))
        raw_amounts = np.random.lognormal(mean, sigma, size=n_transactions)
    elif distribution_model == 'gaussian':
        mean = float(model_cfg.get('mean', 3500.0))
        std = float(model_cfg.get('std', 1400.0))
        raw_amounts = np.random.normal(mean, std, size=n_transactions)
    else:  # Uniform fallback
        raw_amounts = np.random.uniform(r_min, min(r_max, 50000.0), size=n_transactions)

    # Fast timestamp generation
    now_ts = int(datetime.now().timestamp())
    sec_in_day = 86400
    
    transactions = []
    num_accounts = len(accounts)
    
    for i in range(n_transactions):
        account = accounts[random.randint(0, num_accounts - 1)]
        
        # O(1) device lookup
        c_devices = devices_by_customer.get(account['customer_id'])
        device = c_devices[random.randint(0, len(c_devices) - 1)] if c_devices else devices[random.randint(0, len(devices) - 1)]
        
        t_type = sampled_t_types[i]
        t_status = sampled_s_types[i]
        
        # Upper bound based on balance context & rules
        upper_cap = min(account['balance'] + 1000.0, r_max)
        amt = float(np.clip(raw_amounts[i], r_min, upper_cap))
        
        # Generate timestamp in past 180 days with diurnal peak bias
        day_offset = random.randint(0, 180) * sec_in_day
        # Peak around 13:00 (46800s) or 19:30 (70200s)
        peak_base = 46800 if random.random() < 0.45 else 70200
        sec_offset = int(random.gauss(peak_base, 5400)) % sec_in_day
        tx_ts = now_ts - day_offset - sec_offset
        tx_date_str = datetime.fromtimestamp(tx_ts).strftime("%Y-%m-%d %H:%M:%S")
        
        transaction = {
            'transaction_id': f"T{str(i + 1).zfill(7)}",
            'account_id': account['account_id'],
            'device_id': device['device_id'],
            'transaction_type': str(t_type),
            'amount': round(amt, 2),
            'transaction_status': str(t_status),
            'transaction_date': tx_date_str,
            'beneficiary_type': 'INTERNAL',
            'failure_reason': 'NONE' if t_status == 'SUCCESS' else 'UNKNOWN'
        }
        transactions.append(transaction)
        
    return transactions
