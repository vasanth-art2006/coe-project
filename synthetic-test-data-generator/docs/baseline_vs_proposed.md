# Baseline vs Proposed Generator

## Baseline
- Uses pure random generation.
- Often creates referential orphans (devices or accounts without valid customers).
- Fails business constraints (e.g., negative amounts, amounts > balance but marked SUCCESS).
- Poor device/OS matching (e.g. Android running iOS).
- Cannot support manual overrides safely.

## Proposed Generator
- Schema-aware and distribution-aware generation.
- Enforces referential integrity internally.
- Applies strict business constraints before finalizing scenarios.
- Strict mapping of device and OS combinations.
- Comprehensive audit trail and rollback system.
- Zero PII.
