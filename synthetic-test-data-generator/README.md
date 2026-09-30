# Privacy-Safe Synthetic Test Data Generator

## Overview
Automated, privacy-safe test data generation engine designed for mobile banking QA teams. Enforces relational schema boundaries, statistical distributions, business logic, device compatibility, and audit trails.

## Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Running Tests
```bash
pytest tests/ -v
```

## Key Modules
- `validation/pydantic_models.py`: Pydantic v2 schemas for Customer, Account, Device, Transaction, and Scenario.
- `validation/schema_validator.py`: Pydantic validation engine and dataset batch validator.
- `generator/transaction_generator.py`: Pareto, Log-Normal, Gaussian, and Uniform mathematical distribution engines.
- `audit/`: SQLite audit logging for human-in-the-loop manual overrides.
- `rollback/`: Snapshot versioning and point-in-time recovery.
- `legacy/`: Legacy CSV ingestion and migration pipeline.
- `experiments/`: Benchmark comparison against random baseline generators.
- `docs/`: Comprehensive technical documentation and mathematical proofs (`statistical_distributions.md`, `architecture.md`).
