import random
from datetime import datetime
from validation.business_validator import validate_business_rules

def generate_scenarios(customers, accounts, devices, transactions):
    scenarios = []
    
    for i, t in enumerate(transactions):
        account = next((a for a in accounts if a['account_id'] == t['account_id']), None)
        device = next((d for d in devices if d['device_id'] == t['device_id']), None)
        
        if not account or not device:
            continue
            
        scenario_context = {
            'account_status': account['account_status'],
            'amount': t['amount'],
            'balance': account['balance'],
            'device_type': device['device_type'],
            'os_version': device['os_version']
        }
        
        biz_val = validate_business_rules(scenario_context)
        
        expected_result = biz_val['expected_status']
        if not biz_val['is_valid']:
            expected_result = biz_val['expected_failure_reason']
            
        scenario = {
            'scenario_id': f"S{str(i+1).zfill(6)}",
            'customer_id': account['customer_id'],
            'account_id': account['account_id'],
            'device_id': device['device_id'],
            'device_type': device['device_type'],
            'os': device['os'],
            'os_version': device['os_version'],
            'transaction_type': t['transaction_type'],
            'balance': account['balance'],
            'amount': t['amount'],
            'expected_result': expected_result,
            'scenario_category': 'NEGATIVE' if not biz_val['is_valid'] else 'POSITIVE',
            'validation_status': 'PASS',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version': 1
        }
        scenarios.append(scenario)
        
    return scenarios
