import json
import os

def load_schema_rules():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_rules.json')
    with open(path, 'r') as f:
        return json.load(f)

def validate_schema(data, entity_type):
    rules = load_schema_rules().get(entity_type, {})
    errors = []
    
    if entity_type == 'customer':
        if data.get('age') is not None:
            if data['age'] < rules['age']['min'] or data['age'] > rules['age']['max']:
                errors.append(f"Age {data['age']} out of bounds")
        if data.get('risk_level') not in rules['risk_levels']:
            errors.append(f"Invalid risk_level {data.get('risk_level')}")
            
    elif entity_type == 'account':
        if data.get('balance') is not None:
            if data['balance'] < rules['balance']['min']:
                errors.append("Balance cannot be negative")
                
    elif entity_type == 'transaction':
        if data.get('amount') is not None:
            if data['amount'] < rules['amount']['min']:
                errors.append("Amount too low")
                
    return len(errors) == 0, errors
