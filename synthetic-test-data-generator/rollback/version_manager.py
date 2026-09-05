from database.database import get_connection
from audit.audit_logger import AuditLogger
from datetime import datetime

class VersionManager:
    @staticmethod
    def save_initial_version(scenario):
        conn = get_connection()
        conn.execute('''
            INSERT INTO scenario_versions 
            (scenario_id, version, device_type, os, os_version, account_status, balance, transaction_type, amount, expected_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scenario['scenario_id'], 1, scenario['device_type'], scenario['os'], scenario['os_version'], 
            "ACTIVE", # Simplified
            scenario['balance'], scenario['transaction_type'], scenario['amount'], scenario['expected_result'], 
            scenario['created_at']
        ))
        conn.commit()
        conn.close()
        
    @staticmethod
    def create_new_version(scenario_id, field_name, new_value, user, reason):
        conn = get_connection()
        # Get current scenario
        curr = conn.execute("SELECT * FROM test_scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
        if not curr:
            conn.close()
            return False
            
        old_value = curr[field_name]
        new_version = curr['version'] + 1
        
        # Update scenario
        conn.execute(f"UPDATE test_scenarios SET {field_name}=?, version=? WHERE scenario_id=?", (new_value, new_version, scenario_id))
        
        # Get updated scenario for version history
        updated = conn.execute("SELECT * FROM test_scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
        
        # Insert new version
        conn.execute('''
            INSERT INTO scenario_versions 
            (scenario_id, version, device_type, os, os_version, balance, transaction_type, amount, expected_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            updated['scenario_id'], new_version, updated['device_type'], updated['os'], updated['os_version'],
            updated['balance'], updated['transaction_type'], updated['amount'], updated['expected_result'], 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conn.commit()
        conn.close()
        
        AuditLogger.log_action(user, scenario_id, new_version, "OVERRIDE", field_name, old_value, new_value, reason, "PASS")
        return True
        
    @staticmethod
    def rollback_to_version(scenario_id, version, user, reason):
        conn = get_connection()
        target_version = conn.execute("SELECT * FROM scenario_versions WHERE scenario_id=? AND version=?", (scenario_id, version)).fetchone()
        if not target_version:
            conn.close()
            return False
            
        curr = conn.execute("SELECT * FROM test_scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
        old_version = curr['version']
        
        new_version_num = old_version + 1
        
        conn.execute('''
            UPDATE test_scenarios 
            SET device_type=?, os=?, os_version=?, balance=?, transaction_type=?, amount=?, expected_result=?, version=?
            WHERE scenario_id=?
        ''', (
            target_version['device_type'], target_version['os'], target_version['os_version'],
            target_version['balance'], target_version['transaction_type'], target_version['amount'], target_version['expected_result'],
            new_version_num, scenario_id
        ))
        
        # insert rolled back state as new version
        conn.execute('''
            INSERT INTO scenario_versions 
            (scenario_id, version, device_type, os, os_version, balance, transaction_type, amount, expected_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            target_version['scenario_id'], new_version_num, target_version['device_type'], target_version['os'], target_version['os_version'],
            target_version['balance'], target_version['transaction_type'], target_version['amount'], target_version['expected_result'], 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conn.commit()
        conn.close()
        
        AuditLogger.log_action(user, scenario_id, new_version_num, "ROLLBACK", "ALL", f"Version {old_version}", f"Version {version}", reason, "PASS")
        return True
