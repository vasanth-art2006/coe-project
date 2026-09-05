# Data Schema

## Customer
- `customer_id`: TEXT (Primary Key)
- `name`: TEXT
- `age`: INTEGER
- `gender`: TEXT
- `city`: TEXT
- `risk_level`: TEXT
- `email`: TEXT
- `phone`: TEXT
- `customer_status`: TEXT

## Account
- `account_id`: TEXT (Primary Key)
- `customer_id`: TEXT (Foreign Key)
- `account_type`: TEXT
- `balance`: REAL
- `currency`: TEXT
- `account_status`: TEXT

## Device
- `device_id`: TEXT (Primary Key)
- `customer_id`: TEXT (Foreign Key)
- `device_type`: TEXT
- `manufacturer`: TEXT
- `model`: TEXT
- `os`: TEXT
- `os_version`: TEXT
- `app_version`: TEXT
- `device_status`: TEXT

## Transaction
- `transaction_id`: TEXT (Primary Key)
- `account_id`: TEXT (Foreign Key)
- `device_id`: TEXT (Foreign Key)
- `transaction_type`: TEXT
- `amount`: REAL
- `transaction_status`: TEXT
- `transaction_date`: TEXT
- `beneficiary_type`: TEXT
- `failure_reason`: TEXT

## Test Scenario
- `scenario_id`: TEXT (Primary Key)
- `customer_id`: TEXT
- `account_id`: TEXT
- `device_id`: TEXT
- `device_type`: TEXT
- `os`: TEXT
- `os_version`: TEXT
- `transaction_type`: TEXT
- `balance`: REAL
- `amount`: REAL
- `expected_result`: TEXT
- `scenario_category`: TEXT
- `validation_status`: TEXT
- `created_at`: TEXT
- `version`: INTEGER
