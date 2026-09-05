import json
import os

def load_business_rules():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'business_rules.json')
    with open(path, 'r') as f:
        return json.load(f).get('rules', [])

def evaluate_condition(condition, context):
    try:
        return eval(condition, {}, context)
    except Exception as e:
        return False

def validate_business_rules(scenario_context):
    rules = load_business_rules()
    errors = []
    expected_failure_reason = None
    expected_status = "SUCCESS"
    
    for rule in rules:
        if evaluate_condition(rule['condition'], scenario_context):
            errors.append(rule['id'])
            if 'enforce_failure_reason' in rule:
                expected_failure_reason = rule['enforce_failure_reason']
            if 'enforce_transaction_status' in rule:
                expected_status = rule['enforce_transaction_status']
                
    return {
        'is_valid': len(errors) == 0,
        'violated_rules': errors,
        'expected_status': expected_status,
        'expected_failure_reason': expected_failure_reason
    }
