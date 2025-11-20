"""Composition root for dependency injection.

This module provides factory functions to wire up dependencies.
"""

from app.domain.services import LinkTokenService, PolicyEnforcer
from app.application.use_cases.create_link_token import CreateLinkTokenUseCase
from app.adapters.inmemory.user_repo import InMemoryUserRepository
from app.adapters.inmemory.link_token_repo import InMemoryLinkTokenRepository
from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistry
from app.adapters.inmemory.audit import InMemoryAuditLog


def build_link_token_service_with_inmemory_adapters() -> LinkTokenService:
    """Build a LinkTokenService with in-memory adapters for testing.

    Returns:
        A configured LinkTokenService instance.
    """
    user_repository = InMemoryUserRepository()
    link_token_repository = InMemoryLinkTokenRepository()
    audit_log = InMemoryAuditLog()
    policy_enforcer = PolicyEnforcer()

    return LinkTokenService(
        link_token_port=link_token_repository,
        user_repository=user_repository,
        audit_port=audit_log,
        policy_enforcer=policy_enforcer,
    )


def build_create_link_token_use_case_with_inmemory_adapters() -> CreateLinkTokenUseCase:
    """Build a CreateLinkTokenUseCase with in-memory adapters for testing.

    Returns:
        A configured CreateLinkTokenUseCase instance.
    """
    link_token_service = build_link_token_service_with_inmemory_adapters()
    return CreateLinkTokenUseCase(link_token_service=link_token_service)


def build_app():
    """Build the application with all dependencies wired up.

    This function can be used in tests to get a fully configured application.

    Returns:
        A dictionary containing all configured services and use cases.
    """
    user_repository = InMemoryUserRepository()
    link_token_repository = InMemoryLinkTokenRepository()
    wallet_registry = InMemoryWalletRegistry()
    audit_log = InMemoryAuditLog()
    policy_enforcer = PolicyEnforcer()

    link_token_service = LinkTokenService(
        link_token_port=link_token_repository,
        user_repository=user_repository,
        audit_port=audit_log,
        policy_enforcer=policy_enforcer,
    )

    create_link_token_use_case = CreateLinkTokenUseCase(link_token_service=link_token_service)

    return {
        "user_repository": user_repository,
        "link_token_repository": link_token_repository,
        "wallet_registry": wallet_registry,
        "audit_log": audit_log,
        "policy_enforcer": policy_enforcer,
        "link_token_service": link_token_service,
        "create_link_token_use_case": create_link_token_use_case,
    }
