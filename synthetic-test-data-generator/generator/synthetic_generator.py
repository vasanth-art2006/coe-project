from .customer_generator import generate_customers
from .account_generator import generate_accounts
from .device_generator import generate_devices
from .transaction_generator import generate_transactions
from .scenario_generator import generate_scenarios

class SyntheticGenerator:
    def __init__(self, seed=None):
        self.seed = seed
        
    def generate_dataset(self, n_scenarios):
        # Rough heuristic: n_scenarios is the number of transactions
        # We need roughly enough customers, accounts, devices.
        n_customers = max(10, n_scenarios // 5)
        n_accounts = n_customers
        n_devices = n_customers
        
        customers = generate_customers(n_customers, self.seed)
        accounts = generate_accounts(customers, n_accounts)
        devices = generate_devices(customers, n_devices)
        transactions = generate_transactions(accounts, devices, n_scenarios)
        
        scenarios = generate_scenarios(customers, accounts, devices, transactions)
        
        return {
            'customers': customers,
            'accounts': accounts,
            'devices': devices,
            'transactions': transactions,
            'scenarios': scenarios
        }
