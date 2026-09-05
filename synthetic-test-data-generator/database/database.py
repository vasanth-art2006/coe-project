import sqlite3
import os

DB_PATH = "data/synthetic_data.db"

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        schema = f.read()
    conn.executescript(schema)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
