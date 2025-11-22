"""
CRUD operations module.
Exports all CRUD functions for User, Project, Milestone, Transaction, and KYC models.
"""

# User CRUD operations
from app.crud.user import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_users,
    update_user,
    delete_user,
)

# Project CRUD operations
from app.crud.project import (
    create_project,
    get_project_by_id,
    get_projects,
    get_projects_by_user,
    update_project,
    delete_project,
)

# Milestone CRUD operations
from app.crud.milestone import (
    create_milestone,
    get_milestone_by_id,
    get_milestones,
    get_milestones_by_project,
    update_milestone,
    delete_milestone,
    mark_milestone_completed,
    mark_milestone_approved,
    mark_milestone_paid,
)

# Transaction CRUD operations
from app.crud.transaction import (
    create_transaction,
    get_transaction_by_id,
    get_transaction_by_gateway_id,
    get_transactions,
    get_transactions_by_user,
    get_transactions_by_project,
    update_transaction,
    delete_transaction,
    update_transaction_status,
)

# KYC CRUD operations
from app.crud.kyc import (
    hash_security_code,
    hash_approval_code,
    create_kyc_submission,
    get_kyc_by_user,
    get_kyc_by_id,
    update_kyc_status,
    get_all_kyc_submissions,
)

__all__ = [
    # User
    "create_user",
    "get_user_by_id",
    "get_user_by_email",
    "get_users",
    "update_user",
    "delete_user",
    # Project
    "create_project",
    "get_project_by_id",
    "get_projects",
    "get_projects_by_user",
    "update_project",
    "delete_project",
    # Milestone
    "create_milestone",
    "get_milestone_by_id",
    "get_milestones",
    "get_milestones_by_project",
    "update_milestone",
    "delete_milestone",
    "mark_milestone_completed",
    "mark_milestone_approved",
    "mark_milestone_paid",
    # Transaction
    "create_transaction",
    "get_transaction_by_id",
    "get_transaction_by_gateway_id",
    "get_transactions",
    "get_transactions_by_user",
    "get_transactions_by_project",
    "update_transaction",
    "delete_transaction",
    "update_transaction_status",
    # KYC
    "hash_security_code",
    "hash_approval_code",
    "create_kyc_submission",
    "get_kyc_by_user",
    "get_kyc_by_id",
    "update_kyc_status",
    "get_all_kyc_submissions",
]
