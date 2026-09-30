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

## Key Documentation
- `docs/unit_testing_and_error_boundaries.md`: Complete 68-test taxonomy and boundary analysis.
- `docs/statistical_distributions.md`: Mathematical formulations for Pareto, Log-Normal, Gaussian, and Diurnal models.
- `docs/architecture.md`: System pipeline specification and subsystem decomposition.

## Key Modules & APIs
- `validation/pydantic_models.py`: Pydantic v2 schemas (`CustomerModel`, `AccountModel`, `DeviceModel`, `TransactionModel`, `ScenarioModel`).
- `validation/schema_validator.py`: Pydantic validation engine and `validate_dataset_pydantic()`.
- `generator/transaction_generator.py`: Pareto, Log-Normal, Gaussian mathematical distribution engines.
- `audit/`: SQLite audit logging for human-in-the-loop manual overrides.
- `rollback/version_manager.py`: Point-in-time recovery and snapshot versioning.
- `legacy/legacy_migrator.py`: Legacy CSV ingestion and migration pipeline.
- `experiments/benchmark.py`: Benchmark comparison against random baseline generators.
