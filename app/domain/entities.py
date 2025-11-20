"""Domain entities for the Amani backend.

This module contains pure domain entities without framework dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    CLIENT = "client"
    FREELANCER = "freelancer"
    ADMIN = "admin"


class LinkTokenStatus(str, Enum):
    """Link token status enumeration."""

    PENDING = "pending"
    CONSUMED = "consumed"
    EXPIRED = "expired"


class WalletProvider(str, Enum):
    """Wallet provider enumeration."""

    PLAID = "plaid"
    FINCRA = "fincra"


@dataclass
class User:
    """Domain entity representing a user."""

    id: str
    external_id: str
    email: str
    role: UserRole
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LinkToken:
    """Domain entity representing a link token for wallet connection."""

    id: str
    user_id: str
    token: str
    provider: WalletProvider
    status: LinkTokenStatus = LinkTokenStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    consumed_at: Optional[datetime] = None


@dataclass
class WalletRegistryEntry:
    """Domain entity representing a wallet registry entry."""

    id: str
    user_id: str
    provider: WalletProvider
    provider_account_id: str
    access_token: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Hold:
    """Domain entity representing a hold on funds."""

    id: str
    user_id: str
    amount: float
    currency: str
    reason: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    released_at: Optional[datetime] = None


@dataclass
class LedgerEntry:
    """Domain entity representing a ledger entry for transactions."""

    id: str
    user_id: str
    amount: float
    currency: str
    entry_type: str
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None
