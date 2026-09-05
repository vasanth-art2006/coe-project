# Demo Script

1. **Explain problem**: Manual data generation is slow and error-prone.
2. **Show baseline**: Navigate to Baseline vs Proposed.
3. **Generate synthetic scenarios**: Go to Generate Test Data, generate 100 records.
4. **Show validation**: Navigate to Validation to show 100% pass on privacy, referential, schema, and business rules.
5. **Demonstrate insufficient funds**: Go to Generated Scenarios, filter by NEGATIVE category where `expected_result` = INSUFFICIENT_FUNDS.
6. **Demonstrate manual override**: Go to Manual Override, change an amount to force a failure, provide reason.
7. **Show audit trail**: Check Audit Trail for the logged override.
8. **Demonstrate rollback**: Go to Rollback, select the scenario, and revert the amount.
9. **Import legacy data**: Go to Legacy Migration, migrate the CSV.
10. **Run Benchmark**: Go to Experiment and execute the benchmark.
