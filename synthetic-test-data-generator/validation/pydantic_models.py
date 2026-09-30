"""
Pydantic v2 Schema Validation Engine for Banking Entities.
Enforces strict type safety, boundary constraints, enum validations,
and cross-field consistency for Customers, Accounts, Devices, Transactions, and Scenarios.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import re

# ─────────────────────────────────────────────────────────
# 1. CUSTOMER SCHEMAS
# ─────────────────────────────────────────────────────────
class CustomerValidationSchema(BaseModel):
    """Flexible validator for partial or full customer data against schema rules."""
    model_config = ConfigDict(extra="ignore")

    customer_id: Optional[str] = Field(default=None, pattern=r"^C\d{4,7}$")
    name: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=18, le=80, description="Customer age must be between 18 and 80")
    gender: Optional[Literal["M", "F", "Other"]] = None
    city: Optional[str] = None
    risk_level: Optional[Literal["LOW", "MEDIUM", "HIGH"]] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    customer_status: Optional[Literal["ACTIVE", "INACTIVE"]] = None

    @field_validator("email")
    @classmethod
    def validate_synthetic_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Must not contain common real public domains
            blocked = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
            for dom in blocked:
                if dom in v.lower():
                    raise ValueError(f"Real public domain {dom} detected in synthetic data")
        return v

    @field_validator("phone")
    @classmethod
    def validate_synthetic_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            digits = re.sub(r"\D", "", v)
            if not digits.startswith("555") and not digits.startswith("1555"):
                raise ValueError("Synthetic phone numbers must use reserved 555 prefix")
        return v


class CustomerModel(CustomerValidationSchema):
    """Complete Customer entity model with required core fields."""
    customer_id: str = Field(pattern=r"^C\d{4,7}$")
    name: str = Field(min_length=2)
    age: int = Field(ge=18, le=80)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    email: str
    phone: str
    customer_status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


# ─────────────────────────────────────────────────────────
# 2. ACCOUNT SCHEMAS
# ─────────────────────────────────────────────────────────
class AccountValidationSchema(BaseModel):
    """Flexible validator for partial or full account data."""
    model_config = ConfigDict(extra="ignore")

    account_id: Optional[str] = Field(default=None, pattern=r"^A\d{4,7}$")
    customer_id: Optional[str] = Field(default=None, pattern=r"^C\d{4,7}$")
    account_type: Optional[Literal["SAVINGS", "CURRENT", "SALARY", "FIXED_DEPOSIT"]] = None
    balance: Optional[float] = Field(default=None, ge=0.0, le=1000000.0, description="Balance must be non-negative up to 1,000,000")
    currency: Optional[Literal["INR", "USD", "EUR", "GBP"]] = "INR"
    account_status: Optional[Literal["ACTIVE", "BLOCKED", "CLOSED"]] = None


class AccountModel(AccountValidationSchema):
    """Complete Account entity model."""
    account_id: str = Field(pattern=r"^A\d{4,7}$")
    customer_id: str = Field(pattern=r"^C\d{4,7}$")
    account_type: Literal["SAVINGS", "CURRENT", "SALARY", "FIXED_DEPOSIT"]
    balance: float = Field(ge=0.0, le=1000000.0)
    currency: Literal["INR", "USD", "EUR", "GBP"] = "INR"
    account_status: Literal["ACTIVE", "BLOCKED", "CLOSED"] = "ACTIVE"


# ─────────────────────────────────────────────────────────
# 3. DEVICE SCHEMAS
# ─────────────────────────────────────────────────────────
VALID_DEVICE_OS_MAP = {
    "iPhone": ["iOS 16", "iOS 17", "iOS 18"],
    "Android Mobile": ["Android 11", "Android 12", "Android 13", "Android 14", "Android 15"],
    "Low-end Android": ["Android 10", "Android 11", "Android 12"],
    "Tablet": ["Android 12", "Android 13", "Android 14", "iPadOS 16", "iPadOS 17", "iPadOS 18"]
}

class DeviceValidationSchema(BaseModel):
    """Flexible validator for device entity."""
    model_config = ConfigDict(extra="ignore")

    device_id: Optional[str] = Field(default=None, pattern=r"^D\d{4,7}$")
    customer_id: Optional[str] = Field(default=None, pattern=r"^C\d{4,7}$")
    device_type: Optional[Literal["Android Mobile", "iPhone", "Tablet", "Low-end Android", "iPad"]] = None
    os: Optional[Literal["Android", "iOS", "iPadOS"]] = None
    os_version: Optional[str] = None

    @model_validator(mode="after")
    def validate_device_os_compatibility(self):
        if self.device_type and self.os_version:
            allowed = VALID_DEVICE_OS_MAP.get(self.device_type, [])
            allowed_short = [v.split(' ')[-1] for v in allowed]
            full_combo = f"{self.os} {self.os_version}".strip() if self.os and not self.os_version.startswith(self.os) else self.os_version
            
            if self.os_version not in allowed and self.os_version not in allowed_short and full_combo not in allowed:
                raise ValueError(
                    f"Incompatible device/OS combo: {self.device_type} cannot run {self.os_version}. "
                    f"Allowed versions: {allowed}"
                )
        if self.device_type == "iPhone" and self.os and self.os != "iOS":
            raise ValueError(f"iPhone cannot have OS {self.os}")
        return self


class DeviceModel(DeviceValidationSchema):
    """Complete Device entity model."""
    device_id: str = Field(pattern=r"^D\d{4,7}$")
    customer_id: str = Field(pattern=r"^C\d{4,7}$")
    device_type: Literal["Android Mobile", "iPhone", "Tablet", "Low-end Android", "iPad"]
    os: Literal["Android", "iOS", "iPadOS"]
    os_version: str


# ─────────────────────────────────────────────────────────
# 4. TRANSACTION SCHEMAS
# ─────────────────────────────────────────────────────────
class TransactionValidationSchema(BaseModel):
    """Flexible validator for transaction entity."""
    model_config = ConfigDict(extra="ignore")

    transaction_id: Optional[str] = Field(default=None, pattern=r"^T\d{4,9}$")
    account_id: Optional[str] = Field(default=None, pattern=r"^A\d{4,7}$")
    device_id: Optional[str] = Field(default=None, pattern=r"^D\d{4,7}$")
    transaction_type: Optional[Literal["UPI", "CARD", "TRANSFER", "BILL_PAYMENT", "ATM"]] = None
    amount: Optional[float] = Field(default=None, ge=1.0, le=500000.0, description="Amount must be between 1 and 500,000")
    transaction_status: Optional[Literal["SUCCESS", "FAILED", "PENDING"]] = None
    transaction_date: Optional[str] = None
    beneficiary_type: Optional[str] = "INTERNAL"
    failure_reason: Optional[str] = "NONE"


class TransactionModel(TransactionValidationSchema):
    """Complete Transaction entity model."""
    transaction_id: str = Field(pattern=r"^T\d{4,9}$")
    account_id: str = Field(pattern=r"^A\d{4,7}$")
    device_id: str = Field(pattern=r"^D\d{4,7}$")
    transaction_type: Literal["UPI", "CARD", "TRANSFER", "BILL_PAYMENT", "ATM"]
    amount: float = Field(ge=1.0, le=500000.0)
    transaction_status: Literal["SUCCESS", "FAILED", "PENDING"]
    transaction_date: str
    beneficiary_type: str = "INTERNAL"
    failure_reason: str = "NONE"


# ─────────────────────────────────────────────────────────
# 5. SCENARIO SCHEMA
# ─────────────────────────────────────────────────────────
class ScenarioModel(BaseModel):
    """Complete Test Scenario model synthesized from all entities."""
    model_config = ConfigDict(extra="ignore")

    scenario_id: str = Field(pattern=r"^S\d{4,8}$")
    customer_id: str
    account_id: str
    device_id: str
    device_type: str
    os: str
    os_version: str
    transaction_type: str
    balance: float
    amount: float
    expected_result: str
    scenario_category: Literal["POSITIVE", "NEGATIVE"]
    validation_status: str = "PASS"
    created_at: str
    version: int = 1
