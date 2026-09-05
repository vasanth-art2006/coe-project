import json
import os
import random
from faker import Faker

fake = Faker()

def load_schema_rules():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_rules.json')
    with open(path, 'r') as f:
        return json.load(f)

def generate_customers(n, seed=None):
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
        
    rules = load_schema_rules()['customer']
    customers = []
    
    for i in range(1, n + 1):
        customer = {
            'customer_id': f"C{str(i).zfill(5)}",
            'name': fake.name(),
            'age': random.randint(rules['age']['min'], rules['age']['max']),
            'gender': random.choice(["M", "F", "Other"]),
            'city': fake.city(),
            'risk_level': random.choice(rules['risk_levels']),
            'email': fake.email(domain="synthetic-test.local"),
            'phone': f"555{random.randint(1000000, 9999999)}",
            'customer_status': random.choice(rules['status'])
        }
        customers.append(customer)
        
    return customers
