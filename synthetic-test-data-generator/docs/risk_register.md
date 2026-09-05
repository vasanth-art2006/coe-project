# Risk Register

1. **Privacy Leakage**
   - *Likelihood*: Low (Faker is deterministic and purely synthetic).
   - *Mitigation*: Run Privacy Validator on all generated fields before export.

2. **Unrealistic synthetic data**
   - *Likelihood*: Medium
   - *Mitigation*: Adjust `distributions.json` based on real production analytics.

3. **Referential integrity failure**
   - *Likelihood*: Low
   - *Mitigation*: Implemented SQLite foreign keys and application-level referential validators.

4. **Manual override misuse**
   - *Likelihood*: Medium
   - *Mitigation*: Audit trails track 'who, when, what, why'. Rollback functionality provides a safety net.
