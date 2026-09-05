import random
from datetime import datetime

class BaselineGenerator:
    @staticmethod
    def generate(n_scenarios):
        scenarios = []
        devices = ["Phone", "Tablet", "Desktop", "Smartwatch"]
        os_list = ["Android 9", "Android 10", "iOS 14", "Windows", "Symbian"]
        tx_types = ["UPI", "CARD", "NEFT", "RTGS"]
        
        for i in range(n_scenarios):
            scenario = {
                'scenario_id': f"B{str(i).zfill(5)}",
                'customer_id': f"C_{random.randint(1,100)}",
                'account_id': f"A_{random.randint(1,100)}",
                'device_id': f"D_{random.randint(1,100)}",
                'device_type': random.choice(devices),
                'os': random.choice(os_list),
                'os_version': "Unknown",
                'transaction_type': random.choice(tx_types),
                'balance': random.uniform(10, 10000),
                'amount': random.uniform(-100, 20000), # includes invalid negative amounts
                'expected_result': random.choice(["SUCCESS", "FAILED"]),
                'scenario_category': 'RANDOM',
                'validation_status': 'UNKNOWN',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'version': 1
            }
            scenarios.append(scenario)
            
        return scenarios
