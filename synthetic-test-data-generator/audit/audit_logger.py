import uuid
from datetime import datetime
from database.database import get_connection

class AuditLogger:
    @staticmethod
    def log_action(user, scenario_id, version, action, field_name=None, old_value=None, new_value=None, reason=None, validation_status=None):
        conn = get_connection()
        audit_id = f"AUD_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute('''
            INSERT INTO audit_logs 
            (audit_id, timestamp, user, scenario_id, version, action, field_name, old_value, new_value, reason, validation_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (audit_id, timestamp, user, scenario_id, version, action, field_name, str(old_value), str(new_value), reason, validation_status))
        
        conn.commit()
        conn.close()
