"""Composition root - wires dependencies for different environments."""

from app.domain.services import LinkTokenService, PolicyEnforcer
from app.ports.link_token import LinkTokenPort
from app.ports.audit import AuditPort
from app.adapters.inmemory.link_token_repo import InMemoryLinkTokenRepository
from app.adapters.inmemory.audit import InMemoryAudit
from app.application.use_cases.create_link_token import CreateLinkTokenUseCase


def build_in_memory_services():
    """Build services with in-memory adapters for testing.

    Returns:
        Dictionary of services and use cases
    """
    # Create adapters
    link_token_port: LinkTokenPort = InMemoryLinkTokenRepository()
    audit_port: AuditPort = InMemoryAudit()

    # Create domain services
    policy_enforcer = PolicyEnforcer()
    link_token_service = LinkTokenService(
        link_token_port=link_token_port,
        audit_port=audit_port,
        policy_enforcer=policy_enforcer,
    )

    # Create use cases
    create_link_token_use_case = CreateLinkTokenUseCase(link_token_service=link_token_service)

    return {
        "link_token_service": link_token_service,
        "create_link_token_use_case": create_link_token_use_case,
        "link_token_port": link_token_port,
        "audit_port": audit_port,
        "policy_enforcer": policy_enforcer,
    }


def build_app():
    """Build application with in-memory adapters (for testing).

    Returns:
        Application services
    """
    return build_in_memory_services()
