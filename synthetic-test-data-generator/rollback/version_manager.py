"""
Version Management and Rollback Engine for Test Scenarios.

Provides point-in-time state snapshotting and version rollback capabilities
for synthetic banking test scenarios. All manual modifications create an
immutable version history record in SQLite and log an event in the audit trail.
"""
from typing import Optional, Dict, Any
from database.database import get_connection
from audit.audit_logger import AuditLogger
from datetime import datetime

class VersionManager:
    """
    Manages scenario snapshot lifecycles, incremental version increments,
    and single-click rollbacks to historical versions.
    """

    @staticmethod
    def save_initial_version(scenario: Dict[str, Any]) -> None:
        """
        Snapshot the initial baseline version (Version 1) of a freshly generated test scenario.

        Args:
            scenario: Dictionary representing the synthesized test scenario.
        """
        conn = get_connection()
        conn.execute('''
            INSERT INTO scenario_versions 
            (scenario_id, version, device_type, os, os_version, account_status, balance, transaction_type, amount, expected_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scenario['scenario_id'], 1, scenario['device_type'], scenario['os'], scenario['os_version'], 
            "ACTIVE", # Default initial account condition
            scenario['balance'], scenario['transaction_type'], scenario['amount'], scenario['expected_result'], 
            scenario['created_at']
        ))
        conn.commit()
        conn.close()
        
    @staticmethod
    def create_new_version(scenario_id: str, field_name: str, new_value: Any, user: str, reason: str) -> bool:
        """
        Apply a human-in-the-loop manual override to an existing scenario.
        Increments the version number, preserves previous state in `scenario_versions`,
        updates active `test_scenarios` record, and writes an audit event.

        Args:
            scenario_id: Unique identifier of scenario being overridden (e.g., 'S000001').
            field_name: Column/field name being updated (e.g., 'amount', 'balance').
            new_value: New value to apply.
            user: Username or identifier of tester performing the override.
            reason: Justification note for audit and compliance tracking.

        Returns:
            bool: True if override and versioning succeeded, False if scenario not found.
        """
        conn = get_connection()
        # Retrieve current scenario state prior to modification
        curr = conn.execute("SELECT * FROM test_scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
        if not curr:
            conn.close()
            return False
            
        old_value = curr[field_name]
        new_version = curr['version'] + 1
        
        # Update the active scenario record with new value and incremented version
        conn.execute(f"UPDATE test_scenarios SET {field_name}=?, version=? WHERE scenario_id=?", (new_value, new_version, scenario_id))
        
        # Retrieve the updated scenario row for complete version history preservation
        updated = conn.execute("SELECT * FROM test_scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
        
        # Insert new point-in-time snapshot into historical scenario_versions table
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
        
        # Log auditable action in SQLite audit_logs table
        AuditLogger.log_action(user, scenario_id, new_version, "OVERRIDE", field_name, str(old_value), str(new_value), reason, "PASS")
        return True
        
    @staticmethod
    def rollback_to_version(scenario_id: str, version: int, user: str, reason: str) -> bool:
        """
        Roll back a test scenario to an exact prior version snapshot.
        Restores device, balance, amount, and result fields, updates active version,
        and logs a ROLLBACK event to the audit trail.

        Args:
            scenario_id: Target scenario identifier.
            version: Target historical version number to restore.
            user: Username of tester initiating the rollback.
            reason: Operational justification for rollback.

        Returns:
            bool: True if rollback succeeded, False if target version not found.
        """
        conn = get_connection()
        target_version = conn.execute(
            "SELECT * FROM scenario_versions WHERE scenario_id=? AND version=?", 
            (scenario_id, version)
        ).fetchone()
        
        if not target_version:
            conn.close()
            return False
            
        curr = conn.execute("SELECT * FROM test_scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
        old_version = curr['version'] if curr else 0
        new_version = old_version + 1
        
        # Restore target version parameters into active test_scenarios record
        conn.execute('''
            UPDATE test_scenarios 
            SET device_type=?, os=?, os_version=?, balance=?, transaction_type=?, amount=?, expected_result=?, version=?
            WHERE scenario_id=?
        ''', (
            target_version['device_type'], target_version['os'], target_version['os_version'],
            target_version['balance'], target_version['transaction_type'], target_version['amount'],
            target_version['expected_result'], new_version, scenario_id
        ))
        
        # Snapshot the newly restored state as the current active version in history
        conn.execute('''
            INSERT INTO scenario_versions 
            (scenario_id, version, device_type, os, os_version, balance, transaction_type, amount, expected_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scenario_id, new_version, target_version['device_type'], target_version['os'], target_version['os_version'],
            target_version['balance'], target_version['transaction_type'], target_version['amount'],
            target_version['expected_result'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conn.commit()
        conn.close()
        
        # Log rollback operation to audit trail
        AuditLogger.log_action(
            user, scenario_id, new_version, "ROLLBACK", "version", 
            str(old_version), str(version), f"Rollback to v{version}: {reason}", "PASS"
        )
        return True
