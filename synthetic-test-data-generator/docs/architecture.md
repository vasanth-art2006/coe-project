# Architecture

## System Overview
The Synthetic Test Data Generator is a modular Python system built with Streamlit, SQLite, Pandas, and Pydantic. It generates realistic, privacy-safe testing scenarios for mobile banking apps.

## Components
1. **Generator Engine**: Uses Faker and Numpy for distribution-aware generation.
2. **Validation Engine**: Enforces schema rules, business logic, referential integrity, and privacy checks.
3. **Audit & Rollback**: Tracks changes and manages versioning via SQLite.
4. **Legacy Migrator**: Converts older CSV formats into the new schema.
5. **Baseline**: Naive random generator for benchmarking.

## Data Flow
Configuration -> Generator -> Scenarios -> Validator -> Database -> Streamlit UI -> Export
