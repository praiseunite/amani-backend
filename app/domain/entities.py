"""Domain entities - pure business objects without framework dependencies."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class WalletProvider(str, Enum):
    """Supported wallet providers."""

    FINCRA = "fincra"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"


class HoldStatus(str, Enum):
    """Status of a hold on funds."""

    ACTIVE = "active"
    RELEASED = "released"
    CAPTURED = "captured"


class TransactionType(str, Enum):
    """Type of ledger transaction."""

    DEBIT = "debit"
    CREDIT = "credit"


@dataclass
class User:
    """User entity representing a platform user."""

    id: UUID = field(default_factory=uuid4)
    external_id: Optional[str] = None
    email: str = ""
    full_name: Optional[str] = None
    role: str = "client"
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LinkToken:
    """Link token for connecting external wallets."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    token: str = ""
    provider: WalletProvider = WalletProvider.FINCRA
    expires_at: datetime = field(default_factory=datetime.utcnow)
    is_consumed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    consumed_at: Optional[datetime] = None


@dataclass
class WalletRegistryEntry:
    """Registry entry for a connected wallet."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    provider: WalletProvider = WalletProvider.FINCRA
    provider_account_id: str = ""
    provider_customer_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Hold:
    """Hold on funds in escrow."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    amount: float = 0.0
    currency: str = "USD"
    status: HoldStatus = HoldStatus.ACTIVE
    reference: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    released_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None


@dataclass
class LedgerEntry:
    """Ledger entry for accounting purposes."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    transaction_type: TransactionType = TransactionType.CREDIT
    amount: float = 0.0
    currency: str = "USD"
    balance_after: float = 0.0
    reference: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
