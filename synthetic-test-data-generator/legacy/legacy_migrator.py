import pandas as pd
import os
import shutil

class LegacyMigrator:
    @staticmethod
    def migrate(legacy_csv_path):
        # backup
        backup_path = legacy_csv_path + ".bak"
        shutil.copy(legacy_csv_path, backup_path)
        
        df = pd.read_csv(legacy_csv_path)
        
        # simple mapping
        mapped = pd.DataFrame()
        mapped['scenario_id'] = [f"LS{str(i).zfill(5)}" for i in range(len(df))]
        mapped['customer_id'] = df['old_customer']
        mapped['account_id'] = df['old_account']
        mapped['device_type'] = df['device'].apply(lambda x: "Android Mobile" if x == "Phone" and df.loc[df['device'] == x, 'os'].values[0] == "Android" else "iPhone")
        mapped['os'] = df['os']
        mapped['os_version'] = "Unknown"
        mapped['transaction_type'] = df['type']
        mapped['amount'] = df['amount']
        mapped['expected_result'] = df['status']
        mapped['balance'] = 100000.0 # dummy
        mapped['device_id'] = [f"LD{str(i).zfill(5)}" for i in range(len(df))]
        
        # export
        out_path = os.path.join(os.path.dirname(legacy_csv_path), "generated", "migrated_legacy_data.csv")
        mapped.to_csv(out_path, index=False)
        return out_path, backup_path
