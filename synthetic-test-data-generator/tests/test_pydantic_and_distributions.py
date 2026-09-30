"""
Dedicated test suite verifying:
1. Pydantic v2 Schema Validation Engine (Models, Field & Model Validators, Batch Validation).
2. Advanced Statistical Distributions (Pareto Power-Law, Log-Normal, Gaussian, Diurnal Timing).
"""
import pytest
import numpy as np
from pydantic import ValidationError

from validation.pydantic_models import (
    CustomerModel,
    CustomerValidationSchema,
    AccountModel,
    AccountValidationSchema,
    DeviceModel,
    DeviceValidationSchema,
    TransactionModel,
    TransactionValidationSchema,
    ScenarioModel,
)
from validation.schema_validator import (
    validate_entity_pydantic,
    validate_dataset_pydantic,
)
from generator.synthetic_generator import SyntheticGenerator
from generator.transaction_generator import generate_transactions

# ─────────────────────────────────────────────────────────
# 1. PYDANTIC SCHEMA VALIDATION ENGINE TESTS
# ─────────────────────────────────────────────────────────
class TestPydanticValidationEngine:
    def test_valid_customer_model_instantiation(self):
        c = CustomerModel(
            customer_id="C00001",
            name="Rahul Sharma",
            age=28,
            risk_level="LOW",
            email="rahul.sharma@synthetic-test.local",
            phone="5551234567",
            customer_status="ACTIVE"
        )
        assert c.customer_id == "C00001"
        assert c.age == 28

    def test_customer_real_domain_blocked_by_pydantic(self):
        with pytest.raises(ValidationError) as exc:
            CustomerModel(
                customer_id="C00002",
                name="Deepan V",
                age=25,
                risk_level="MEDIUM",
                email="deepan@gmail.com",  # Real domain
                phone="5559876543"
            )
        assert "Real public domain gmail.com detected" in str(exc.value)

    def test_customer_invalid_phone_blocked_by_pydantic(self):
        with pytest.raises(ValidationError) as exc:
            CustomerModel(
                customer_id="C00003",
                name="Alice Test",
                age=35,
                risk_level="LOW",
                email="alice@synthetic-test.local",
                phone="9876543210"  # Non-555 phone
            )
        assert "555 prefix" in str(exc.value)

    def test_customer_age_bounds_enforced(self):
        with pytest.raises(ValidationError):
            CustomerModel(
                customer_id="C00004",
                name="Underage User",
                age=17,
                risk_level="HIGH",
                email="test@synthetic-test.local",
                phone="5550001111"
            )

        with pytest.raises(ValidationError):
            CustomerModel(
                customer_id="C00005",
                name="Overage User",
                age=85,
                risk_level="HIGH",
                email="test@synthetic-test.local",
                phone="5550001111"
            )

    def test_account_model_valid(self):
        acc = AccountModel(
            account_id="A00001",
            customer_id="C00001",
            account_type="SAVINGS",
            balance=15000.50,
            currency="INR",
            account_status="ACTIVE"
        )
        assert acc.balance == 15000.50

    def test_account_negative_balance_rejected(self):
        with pytest.raises(ValidationError):
            AccountModel(
                account_id="A00002",
                customer_id="C00001",
                account_type="CURRENT",
                balance=-500.0,
                currency="INR",
                account_status="ACTIVE"
            )

    def test_device_os_mismatch_rejected(self):
        # iPhone cannot run Android
        with pytest.raises(ValidationError) as exc:
            DeviceModel(
                device_id="D00001",
                customer_id="C00001",
                device_type="iPhone",
                os="Android",
                os_version="Android 14"
            )
        assert "cannot run Android 14" in str(exc.value) or "cannot have OS Android" in str(exc.value)

    def test_device_valid_ios_passes(self):
        dev = DeviceModel(
            device_id="D00002",
            customer_id="C00001",
            device_type="iPhone",
            os="iOS",
            os_version="iOS 17"
        )
        assert dev.os_version == "iOS 17"

    def test_transaction_model_bounds(self):
        # Zero amount rejected
        with pytest.raises(ValidationError):
            TransactionModel(
                transaction_id="T0000001",
                account_id="A00001",
                device_id="D00001",
                transaction_type="UPI",
                amount=0.0,
                transaction_status="SUCCESS",
                transaction_date="2026-09-30 12:00:00"
            )

        # Valid transaction passes
        tx = TransactionModel(
            transaction_id="T0000002",
            account_id="A00001",
            device_id="D00001",
            transaction_type="UPI",
            amount=250.75,
            transaction_status="SUCCESS",
            transaction_date="2026-09-30 12:00:00"
        )
        assert tx.amount == 250.75

    def test_batch_dataset_pydantic_validation(self):
        gen = SyntheticGenerator(seed=42)
        dataset = gen.generate_dataset(30)
        summary = validate_dataset_pydantic(dataset)
        assert summary['is_fully_valid'] is True
        assert summary['valid_entities'] == summary['total_entities']
        assert summary['table_metrics']['customer']['validity_pct'] == 100.0
        assert summary['table_metrics']['account']['validity_pct'] == 100.0
        assert summary['table_metrics']['device']['validity_pct'] == 100.0
        assert summary['table_metrics']['transaction']['validity_pct'] == 100.0


# ─────────────────────────────────────────────────────────
# 2. ADVANCED STATISTICAL DISTRIBUTIONS TESTS
# ─────────────────────────────────────────────────────────
class TestStatisticalDistributionsDetailed:
    @pytest.fixture
    def mock_accounts_and_devices(self):
        accs = [
            {'account_id': f'A{str(i).zfill(5)}', 'customer_id': f'C{str(i).zfill(5)}', 'balance': 50000.0, 'account_status': 'ACTIVE'}
            for i in range(1, 20)
        ]
        devs = [
            {'device_id': f'D{str(i).zfill(5)}', 'customer_id': f'C{str(i).zfill(5)}', 'device_type': 'Android Mobile', 'os': 'Android', 'os_version': 'Android 14'}
            for i in range(1, 20)
        ]
        return accs, devs

    def test_pareto_power_law_distribution_properties(self, mock_accounts_and_devices):
        """
        Pareto distribution in banking must have:
        1. Mean > Median (positive right skew).
        2. Majority of transactions (>60%) are below the mean amount.
        """
        accs, devs = mock_accounts_and_devices
        txs = generate_transactions(accs, devs, n_transactions=2000, distribution_model="pareto", seed=42)
        amounts = np.array([t['amount'] for t in txs])

        mean_val = np.mean(amounts)
        median_val = np.median(amounts)

        assert mean_val > median_val, f"Pareto must be right-skewed: mean ({mean_val}) > median ({median_val})"
        
        # In Pareto power-law (alpha=1.8), over 60% of transactions are low-value (below mean)
        below_mean_pct = np.mean(amounts < mean_val)
        assert below_mean_pct > 0.60, f"Expected >60% below mean, got {below_mean_pct*100:.1f}%"

    def test_lognormal_distribution_properties(self, mock_accounts_and_devices):
        """Log-Normal amounts must be strictly positive and exhibit positive skewness."""
        accs, devs = mock_accounts_and_devices
        txs = generate_transactions(accs, devs, n_transactions=1000, distribution_model="lognormal", seed=42)
        amounts = np.array([t['amount'] for t in txs])

        assert np.all(amounts >= 1.0)
        assert np.mean(amounts) > np.median(amounts)

    def test_gaussian_distribution_properties(self, mock_accounts_and_devices):
        """Gaussian distribution amounts must cluster symmetrically around configured mean."""
        accs, devs = mock_accounts_and_devices
        txs = generate_transactions(accs, devs, n_transactions=1500, distribution_model="gaussian", seed=42)
        amounts = np.array([t['amount'] for t in txs])

        mean_val = np.mean(amounts)
        median_val = np.median(amounts)

        # For Gaussian, mean and median are closely aligned (within 10%)
        relative_diff = abs(mean_val - median_val) / mean_val
        assert relative_diff < 0.10, f"Gaussian mean ({mean_val}) and median ({median_val}) should be close"

    def test_diurnal_activity_peak_hours(self, mock_accounts_and_devices):
        """
        Diurnal transaction activity must concentrate during active business hours (8 AM - 11 PM),
        with minimal transactions in deep night (1 AM - 5 AM).
        """
        accs, devs = mock_accounts_and_devices
        txs = generate_transactions(accs, devs, n_transactions=500, distribution_model="pareto", seed=42)
        
        hours = [int(t['transaction_date'].split(' ')[1].split(':')[0]) for t in txs]
        
        daytime_txs = sum(1 for h in hours if 8 <= h <= 23)
        daytime_ratio = daytime_txs / len(hours)

        # More than 85% of transactions should fall between 8 AM and 11 PM
        assert daytime_ratio >= 0.85, f"Expected >=85% daytime transactions, got {daytime_ratio*100:.1f}%"
