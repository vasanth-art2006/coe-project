"""
Schema validation module powered by Pydantic v2.
Validates individual records, partial entities, and entire datasets
against domain rules, type bounds, and cross-field constraints.
"""
import os
import json
from typing import Dict, Any, Tuple, List, Optional
from pydantic import ValidationError
from .pydantic_models import (
    CustomerValidationSchema,
    CustomerModel,
    AccountValidationSchema,
    AccountModel,
    DeviceValidationSchema,
    DeviceModel,
    TransactionValidationSchema,
    TransactionModel,
    ScenarioModel,
)

SCHEMA_MODEL_MAP = {
    'customer': CustomerValidationSchema,
    'account': AccountValidationSchema,
    'device': DeviceValidationSchema,
    'transaction': TransactionValidationSchema,
}

STRICT_MODEL_MAP = {
    'customer': CustomerModel,
    'account': AccountModel,
    'device': DeviceModel,
    'transaction': TransactionModel,
    'scenario': ScenarioModel,
}

def load_schema_rules():
    """Load JSON schema definitions for reference."""
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_rules.json')
    with open(path, 'r') as f:
        return json.load(f)

def validate_schema(data: Dict[str, Any], entity_type: str) -> Tuple[bool, List[str]]:
    """
    Validate data against the specified entity type using Pydantic schema validation.
    
    Args:
        data: Dictionary of entity fields to validate.
        entity_type: One of 'customer', 'account', 'device', 'transaction'.
        
    Returns:
        (is_valid, list_of_error_messages)
    """
    model_cls = SCHEMA_MODEL_MAP.get(entity_type)
    if not model_cls:
        return False, [f"Unknown entity type: {entity_type}"]

    try:
        model_cls(**data)
        return True, []
    except ValidationError as e:
        errors = []
        for err in e.errors():
            field = ".".join(str(loc) for loc in err['loc'])
            msg = err['msg']
            errors.append(f"{field}: {msg}")
        return False, errors

def validate_entity_pydantic(data: Dict[str, Any], entity_type: str, strict: bool = False) -> Tuple[bool, List[str], Optional[Any]]:
    """
    Strict Pydantic validator that returns the parsed Pydantic model instance.
    
    Args:
        data: Entity dictionary
        entity_type: Entity name
        strict: If True, uses the strict full entity model with all required fields.
        
    Returns:
        (is_valid, error_list, parsed_model_or_None)
    """
    map_to_use = STRICT_MODEL_MAP if strict else SCHEMA_MODEL_MAP
    model_cls = map_to_use.get(entity_type)
    if not model_cls:
        return False, [f"Unknown entity type '{entity_type}'"], None

    try:
        instance = model_cls(**data)
        return True, [], instance
    except ValidationError as e:
        errors = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
        return False, errors, None

def validate_dataset_pydantic(dataset: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Validates an entire generated dataset using strict Pydantic models.
    
    Returns a dictionary of summary metrics and errors per table.
    """
    summary = {
        'total_entities': 0,
        'valid_entities': 0,
        'invalid_entities': 0,
        'is_fully_valid': True,
        'table_metrics': {}
    }

    for table_name, model_cls in STRICT_MODEL_MAP.items():
        records = dataset.get(table_name + 's' if table_name != 'scenario' else 'scenarios', [])
        table_total = len(records)
        table_valid = 0
        table_errors = []

        for record in records:
            summary['total_entities'] += 1
            try:
                model_cls(**record)
                table_valid += 1
                summary['valid_entities'] += 1
            except ValidationError as err:
                summary['invalid_entities'] += 1
                summary['is_fully_valid'] = False
                table_errors.append({
                    'id': record.get(f"{table_name}_id", "UNKNOWN"),
                    'errors': [f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in err.errors()]
                })

        summary['table_metrics'][table_name] = {
            'total': table_total,
            'valid': table_valid,
            'invalid': table_total - table_valid,
            'validity_pct': round((table_valid / table_total * 100) if table_total > 0 else 100.0, 2),
            'sample_errors': table_errors[:5]
        }

    return summary
