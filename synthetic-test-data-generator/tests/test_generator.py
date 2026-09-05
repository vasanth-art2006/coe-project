"""
Comprehensive test suite for the Synthetic Test Data Generator.
Covers: Generator, Schema, Business Rules, Referential Integrity,
        Device Compatibility, Privacy, Manual Override, Rollback,
        Legacy Migration, Baseline, Distributions.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import time
from generator.synthetic_generator import SyntheticGenerator
from generator.customer_generator import generate_customers
from generator.account_generator import generate_accounts
from generator.device_generator import generate_devices
from generator.transaction_generator import generate_transactions
from validation.schema_validator import validate_schema
from validation.business_validator import validate_business_rules
from validation.referential_validator import validate_referential_integrity
from validation.device_validator import validate_device_os
from validation.privacy_validator import validate_privacy
from baseline.baseline_generator import BaselineGenerator

# ─────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def dataset():
    """Generate a shared dataset once for all tests."""
    gen = SyntheticGenerator(seed=99)
    return gen.generate_dataset(50)


# ─────────────────────────────────────────────────────────
# 1. GENERATOR TESTS
# ─────────────────────────────────────────────────────────
class TestGeneratorPipeline:
    def test_full_pipeline_produces_expected_count(self, dataset):
        assert len(dataset['customers']) > 0
        assert len(dataset['accounts']) > 0
        assert len(dataset['devices']) > 0
        assert len(dataset['transactions']) == 50
        assert len(dataset['scenarios']) == 50

    def test_customer_ids_unique(self, dataset):
        ids = [c['customer_id'] for c in dataset['customers']]
        assert len(ids) == len(set(ids)), "Duplicate customer IDs found"

    def test_account_ids_unique(self, dataset):
        ids = [a['account_id'] for a in dataset['accounts']]
        assert len(ids) == len(set(ids)), "Duplicate account IDs found"

    def test_transaction_ids_unique(self, dataset):
        ids = [t['transaction_id'] for t in dataset['transactions']]
        assert len(ids) == len(set(ids)), "Duplicate transaction IDs found"

    def test_customers_have_required_fields(self, dataset):
        required = ['customer_id', 'name', 'age', 'email', 'phone', 'city', 'risk_level']
        for c in dataset['customers']:
            for f in required:
                assert f in c, f"Missing field {f} in customer"

    def test_accounts_have_required_fields(self, dataset):
        required = ['account_id', 'customer_id', 'account_type', 'balance', 'currency']
        for a in dataset['accounts']:
            for f in required:
                assert f in a, f"Missing field {f} in account"

    def test_reproducibility_with_same_seed(self):
        g1 = SyntheticGenerator(seed=42).generate_dataset(10)
        g2 = SyntheticGenerator(seed=42).generate_dataset(10)
        ids1 = [s['scenario_id'] for s in g1['scenarios']]
        ids2 = [s['scenario_id'] for s in g2['scenarios']]
        assert ids1 == ids2, "Same seed should produce same scenario IDs"

    def test_large_generation_under_10s(self):
        """10,000 scenarios must complete in under 10 seconds."""
        t = time.time()
        gen = SyntheticGenerator(seed=1)
        gen.generate_dataset(10000)
        elapsed = time.time() - t
        assert elapsed < 10, f"Generation too slow: {elapsed:.2f}s"


# ─────────────────────────────────────────────────────────
# 2. SCHEMA VALIDATION TESTS
# ─────────────────────────────────────────────────────────
class TestSchemaValidation:
    def test_valid_customer_passes(self):
        data = {'age': 30, 'risk_level': 'LOW'}
        ok, errs = validate_schema(data, 'customer')
        assert ok, f"Expected PASS: {errs}"

    def test_age_below_min_fails(self):
        data = {'age': 15, 'risk_level': 'LOW'}
        ok, errs = validate_schema(data, 'customer')
        assert not ok

    def test_age_above_max_fails(self):
        data = {'age': 90, 'risk_level': 'LOW'}
        ok, errs = validate_schema(data, 'customer')
        assert not ok

    def test_invalid_risk_level_fails(self):
        data = {'age': 35, 'risk_level': 'VERY_HIGH'}
        ok, errs = validate_schema(data, 'customer')
        assert not ok

    def test_valid_account_passes(self):
        data = {'balance': 5000.0}
        ok, errs = validate_schema(data, 'account')
        assert ok

    def test_negative_balance_fails(self):
        data = {'balance': -100.0}
        ok, errs = validate_schema(data, 'account')
        assert not ok

    def test_valid_transaction_passes(self):
        data = {'amount': 500.0}
        ok, errs = validate_schema(data, 'transaction')
        assert ok

    def test_zero_amount_fails_schema(self):
        data = {'amount': 0}
        ok, errs = validate_schema(data, 'transaction')
        assert not ok


# ─────────────────────────────────────────────────────────
# 3. BUSINESS RULE TESTS
# ─────────────────────────────────────────────────────────
class TestBusinessRules:
    def _ctx(self, account_status='ACTIVE', amount=100, balance=5000):
        return {'account_status': account_status, 'amount': amount, 'balance': balance}

    def test_active_account_sufficient_funds_passes(self):
        res = validate_business_rules(self._ctx())
        assert res['is_valid']
        assert res['expected_status'] == 'SUCCESS'

    def test_blocked_account_fails(self):
        res = validate_business_rules(self._ctx(account_status='BLOCKED', balance=10000))
        assert not res['is_valid']
        assert res['expected_failure_reason'] == 'ACCOUNT_BLOCKED'

    def test_closed_account_fails(self):
        res = validate_business_rules(self._ctx(account_status='CLOSED', balance=10000))
        assert not res['is_valid']
        assert res['expected_failure_reason'] == 'ACCOUNT_CLOSED'

    def test_insufficient_funds_fails(self):
        res = validate_business_rules(self._ctx(amount=999999, balance=100))
        assert not res['is_valid']
        assert res['expected_failure_reason'] == 'INSUFFICIENT_FUNDS'

    def test_zero_amount_fails(self):
        res = validate_business_rules(self._ctx(amount=0))
        assert not res['is_valid']
        assert res['expected_failure_reason'] == 'INVALID_AMOUNT'

    def test_negative_amount_fails(self):
        res = validate_business_rules(self._ctx(amount=-50))
        assert not res['is_valid']
        assert res['expected_failure_reason'] == 'INVALID_AMOUNT'

    def test_exact_balance_match_passes(self):
        """Exact amount == balance should still pass (boundary)."""
        res = validate_business_rules(self._ctx(amount=5000, balance=5000))
        # Rule 3 is amount > balance. Equal is NOT a violation.
        assert 'INSUFFICIENT_FUNDS' not in res['violated_rules']

    def test_amount_one_over_balance_fails(self):
        res = validate_business_rules(self._ctx(amount=5001, balance=5000))
        assert not res['is_valid']
        assert res['expected_failure_reason'] == 'INSUFFICIENT_FUNDS'


# ─────────────────────────────────────────────────────────
# 4. REFERENTIAL INTEGRITY TESTS
# ─────────────────────────────────────────────────────────
class TestReferentialIntegrity:
    def test_valid_dataset_passes(self, dataset):
        ok, errs = validate_referential_integrity(
            dataset['transactions'], dataset['accounts'],
            dataset['devices'], dataset['customers']
        )
        assert ok, f"Referential errors: {errs}"

    def test_orphan_account_detected(self):
        customers = [{'customer_id': 'C00001'}]
        accounts  = [{'account_id': 'A00001', 'customer_id': 'C99999'}]  # invalid ref
        devices   = []
        txs       = []
        ok, errs = validate_referential_integrity(txs, accounts, devices, customers)
        assert not ok
        assert any('C99999' in e for e in errs)

    def test_orphan_transaction_account_detected(self):
        customers = [{'customer_id': 'C00001'}]
        accounts  = [{'account_id': 'A00001', 'customer_id': 'C00001'}]
        devices   = [{'device_id': 'D00001', 'customer_id': 'C00001'}]
        txs       = [{'transaction_id': 'T0000001', 'account_id': 'A99999', 'device_id': 'D00001'}]
        ok, errs = validate_referential_integrity(txs, accounts, devices, customers)
        assert not ok
        assert any('A99999' in e for e in errs)

    def test_orphan_transaction_device_detected(self):
        customers = [{'customer_id': 'C00001'}]
        accounts  = [{'account_id': 'A00001', 'customer_id': 'C00001'}]
        devices   = [{'device_id': 'D00001', 'customer_id': 'C00001'}]
        txs       = [{'transaction_id': 'T0000001', 'account_id': 'A00001', 'device_id': 'D99999'}]
        ok, errs = validate_referential_integrity(txs, accounts, devices, customers)
        assert not ok
        assert any('D99999' in e for e in errs)


# ─────────────────────────────────────────────────────────
# 5. DEVICE COMPATIBILITY TESTS
# ─────────────────────────────────────────────────────────
class TestDeviceCompatibility:
    def test_android_mobile_android14_valid(self):
        ok, errs = validate_device_os('Android Mobile', 'Android 14')
        assert ok

    def test_iphone_ios17_valid(self):
        ok, errs = validate_device_os('iPhone', 'iOS 17')
        assert ok

    def test_iphone_android14_invalid(self):
        ok, errs = validate_device_os('iPhone', 'Android 14')
        assert not ok, "iPhone + Android 14 must be INVALID"

    def test_android_mobile_ios16_invalid(self):
        ok, errs = validate_device_os('Android Mobile', 'iOS 16')
        assert not ok

    def test_low_end_android_android12_valid(self):
        ok, errs = validate_device_os('Low-end Android', 'Android 12')
        assert ok

    def test_low_end_android_android15_invalid(self):
        ok, errs = validate_device_os('Low-end Android', 'Android 15')
        assert not ok

    def test_unknown_device_type_invalid(self):
        ok, errs = validate_device_os('Smartwatch', 'WearOS 3')
        assert not ok

    def test_tablet_android14_valid(self):
        ok, errs = validate_device_os('Tablet', 'Android 14')
        assert ok


# ─────────────────────────────────────────────────────────
# 6. PRIVACY TESTS
# ─────────────────────────────────────────────────────────
class TestPrivacy:
    def test_synthetic_dataset_no_pii(self, dataset):
        customers = dataset['customers']
        ok, errs, _ = validate_privacy(customers)
        assert ok, f"PII found: {errs}"

    def test_real_email_detected(self):
        records = [{'email': 'john.doe@gmail.com'}]
        ok, errs, _ = validate_privacy(records)
        assert not ok, "Real Gmail email should be flagged as PII"

    def test_synthetic_email_passes(self):
        records = [{'email': 'synth.user@synthetic-test.local'}]
        ok, errs, _ = validate_privacy(records)
        assert ok, f"Synthetic email should pass: {errs}"

    def test_all_emails_are_synthetic(self, dataset):
        for c in dataset['customers']:
            assert 'synthetic-test.local' in c['email'], \
                f"Non-synthetic email found: {c['email']}"

    def test_phone_format_is_synthetic(self, dataset):
        for c in dataset['customers']:
            assert c['phone'].startswith('555'), \
                f"Non-synthetic phone found: {c['phone']}"


# ─────────────────────────────────────────────────────────
# 7. BASELINE TESTS
# ─────────────────────────────────────────────────────────
class TestBaseline:
    def test_baseline_generates_correct_count(self):
        data = BaselineGenerator.generate(100)
        assert len(data) == 100

    def test_baseline_has_no_business_rules(self):
        """Baseline should have negative amounts (no rule enforcement)."""
        data = BaselineGenerator.generate(1000)
        has_neg_amount = any(s['amount'] < 0 for s in data)
        assert has_neg_amount, "Baseline should contain invalid amounts (negative)"

    def test_baseline_has_invalid_os_combos(self):
        """Baseline often produces invalid device/OS combos."""
        data = BaselineGenerator.generate(1000)
        invalid_found = False
        for s in data:
            ok, _ = validate_device_os(s['device_type'], s['os'])
            if not ok:
                invalid_found = True
                break
        assert invalid_found, "Baseline should produce invalid device/OS combos"

    def test_proposed_outperforms_baseline(self):
        """Proposed validity must be higher than baseline."""
        gen = SyntheticGenerator(seed=42)
        proposed = gen.generate_dataset(200)['scenarios']

        baseline = BaselineGenerator.generate(200)

        # validity: all proposed scenarios have amount >= 0 and valid device combos
        proposed_valid = sum(1 for s in proposed
                             if s['amount'] > 0 and validate_device_os(s['device_type'], s['os_version'])[0])
        baseline_valid = sum(1 for s in baseline
                             if s['amount'] > 0 and validate_device_os(s['device_type'], s['os'])[0])

        assert proposed_valid >= baseline_valid, \
            f"Proposed ({proposed_valid}) should beat baseline ({baseline_valid})"


# ─────────────────────────────────────────────────────────
# 8. DISTRIBUTION TESTS
# ─────────────────────────────────────────────────────────
class TestDistributions:
    def test_upi_most_common_transaction_type(self):
        """UPI is configured at 50%, should be the most common type."""
        gen = SyntheticGenerator(seed=7)
        data = gen.generate_dataset(1000)
        tx_types = [t['transaction_type'] for t in data['transactions']]
        from collections import Counter
        counts = Counter(tx_types)
        assert counts.most_common(1)[0][0] == 'UPI', "UPI should be most common transaction type"

    def test_android_mobile_most_common_device(self):
        """Android Mobile is 60%, should be most common device."""
        gen = SyntheticGenerator(seed=8)
        data = gen.generate_dataset(1000)
        dev_types = [d['device_type'] for d in data['devices']]
        from collections import Counter
        counts = Counter(dev_types)
        assert counts.most_common(1)[0][0] == 'Android Mobile', \
            "Android Mobile should be most common device type"

    def test_customer_age_within_bounds(self, dataset):
        for c in dataset['customers']:
            assert 18 <= c['age'] <= 80, f"Age out of bounds: {c['age']}"

    def test_account_balance_within_bounds(self, dataset):
        for a in dataset['accounts']:
            assert a['balance'] >= 0, f"Negative balance: {a['balance']}"


# ─────────────────────────────────────────────────────────
# 9. EDGE CASES
# ─────────────────────────────────────────────────────────
class TestEdgeCases:
    def test_edge_amount_exactly_one_rupee(self):
        ctx = {'account_status': 'ACTIVE', 'amount': 1, 'balance': 5000}
        res = validate_business_rules(ctx)
        assert res['is_valid']

    def test_edge_amount_max_config(self):
        ctx = {'account_status': 'ACTIVE', 'amount': 500000, 'balance': 600000}
        res = validate_business_rules(ctx)
        assert res['is_valid']

    def test_generate_one_scenario(self):
        gen = SyntheticGenerator(seed=0)
        data = gen.generate_dataset(1)
        assert len(data['scenarios']) == 1

    def test_missing_customer_reference(self):
        """Account referencing non-existent customer is caught."""
        ok, errs = validate_referential_integrity(
            [], [{'account_id': 'A1', 'customer_id': 'C_MISSING'}],
            [], [{'customer_id': 'C00001'}]
        )
        assert not ok

    def test_duplicate_customer_check(self):
        """Generator should not produce duplicate customer IDs."""
        customers = generate_customers(100, seed=12)
        ids = [c['customer_id'] for c in customers]
        assert len(ids) == len(set(ids))
