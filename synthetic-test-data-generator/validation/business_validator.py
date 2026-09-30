import json
import os

_RULES_CACHE = None

def load_business_rules():
    global _RULES_CACHE
    if _RULES_CACHE is None:
        path = os.path.join(os.path.dirname(__file__), '..', 'config', 'business_rules.json')
        with open(path, 'r') as f:
            _RULES_CACHE = json.load(f).get('rules', [])
            for r in _RULES_CACHE:
                r['_compiled'] = compile(r['condition'], '<string>', 'eval')
    return _RULES_CACHE

def evaluate_condition(condition, context):
    try:
        if isinstance(condition, dict):
            compiled = condition.get('_compiled')
            if compiled is not None:
                return eval(compiled, {}, context)
            return eval(condition['condition'], {}, context)
        return eval(condition, {}, context)
    except Exception:
        return False

def validate_business_rules(scenario_context):
    rules = load_business_rules()
    errors = []
    expected_failure_reason = None
    expected_status = "SUCCESS"
    
    for rule in rules:
        if evaluate_condition(rule, scenario_context):
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
