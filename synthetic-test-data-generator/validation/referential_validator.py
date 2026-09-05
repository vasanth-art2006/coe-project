def validate_referential_integrity(transactions, accounts, devices, customers):
    errors = []
    customer_ids = {c['customer_id'] for c in customers}
    account_ids = {a['account_id'] for a in accounts}
    device_ids = {d['device_id'] for d in devices}
    
    for a in accounts:
        if a['customer_id'] not in customer_ids:
            errors.append(f"Account {a['account_id']} references missing customer {a['customer_id']}")
            
    for d in devices:
        if d['customer_id'] not in customer_ids:
            errors.append(f"Device {d['device_id']} references missing customer {d['customer_id']}")
            
    for t in transactions:
        if t['account_id'] not in account_ids:
            errors.append(f"Transaction {t['transaction_id']} references missing account {t['account_id']}")
        if t['device_id'] not in device_ids:
            errors.append(f"Transaction {t['transaction_id']} references missing device {t['device_id']}")
            
    return len(errors) == 0, errors
