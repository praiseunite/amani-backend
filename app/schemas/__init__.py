"""Schemas module for Pydantic models."""
from app.schemas.auth import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
    UserUpdate,
    PasswordChange,
    MagicLinkRequest,
    MagicLinkResponse
)
from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse
)
from app.schemas.milestone import (
    MilestoneBase,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneSubmit,
    MilestoneApprove,
    MilestoneResponse,
    MilestoneListResponse
)
from app.schemas.transaction import (
    TransactionBase,
    TransactionCreate,
    EscrowHoldRequest,
    EscrowReleaseRequest,
    TransactionResponse,
    TransactionListResponse
)

__all__ = [
    # Auth schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "UserUpdate",
    "PasswordChange",
    "MagicLinkRequest",
    "MagicLinkResponse",
    # Project schemas
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    # Milestone schemas
    "MilestoneBase",
    "MilestoneCreate",
    "MilestoneUpdate",
    "MilestoneSubmit",
    "MilestoneApprove",
    "MilestoneResponse",
    "MilestoneListResponse",
    # Transaction schemas
    "TransactionBase",
    "TransactionCreate",
    "EscrowHoldRequest",
    "EscrowReleaseRequest",
    "TransactionResponse",
    "TransactionListResponse",
]
