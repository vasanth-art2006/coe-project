import re

PII_PATTERNS = {
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'real_email': r'\b[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook)\.com\b',
}

def validate_privacy(data_list):
    errors = []
    masked_count = 0
    for record in data_list:
        for key, value in record.items():
            if isinstance(value, str):
                for pattern_name, pattern in PII_PATTERNS.items():
                    if re.search(pattern, value, re.IGNORECASE):
                        errors.append(f"Potential PII ({pattern_name}) found in field {key}")
    return len(errors) == 0, errors, masked_count
