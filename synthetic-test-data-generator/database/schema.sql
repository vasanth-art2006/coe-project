CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT,
    age INTEGER,
    gender TEXT,
    city TEXT,
    risk_level TEXT,
    email TEXT,
    phone TEXT,
    customer_status TEXT
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT,
    account_type TEXT,
    balance REAL,
    currency TEXT,
    account_status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    customer_id TEXT,
    device_type TEXT,
    manufacturer TEXT,
    model TEXT,
    os TEXT,
    os_version TEXT,
    app_version TEXT,
    device_status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT,
    device_id TEXT,
    transaction_type TEXT,
    amount REAL,
    transaction_status TEXT,
    transaction_date TEXT,
    beneficiary_type TEXT,
    failure_reason TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE TABLE IF NOT EXISTS test_scenarios (
    scenario_id TEXT PRIMARY KEY,
    customer_id TEXT,
    account_id TEXT,
    device_id TEXT,
    device_type TEXT,
    os TEXT,
    os_version TEXT,
    transaction_type TEXT,
    balance REAL,
    amount REAL,
    expected_result TEXT,
    scenario_category TEXT,
    validation_status TEXT,
    created_at TEXT,
    version INTEGER
);

CREATE TABLE IF NOT EXISTS scenario_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT,
    version INTEGER,
    device_type TEXT,
    os TEXT,
    os_version TEXT,
    account_status TEXT,
    balance REAL,
    transaction_type TEXT,
    amount REAL,
    transaction_status TEXT,
    expected_result TEXT,
    created_at TEXT,
    FOREIGN KEY (scenario_id) REFERENCES test_scenarios(scenario_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id TEXT PRIMARY KEY,
    timestamp TEXT,
    user TEXT,
    scenario_id TEXT,
    version INTEGER,
    action TEXT,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    validation_status TEXT
);
