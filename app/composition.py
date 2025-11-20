"""Composition root - wires dependencies for different environments."""

from app.domain.services import LinkTokenService, PolicyEnforcer, WalletRegistryService
from app.domain.services import LinkTokenService as LinkTokenDomainService
from app.ports.link_token import LinkTokenPort
from app.ports.audit import AuditPort
from app.ports.user_repository import UserRepositoryPort
from app.ports.wallet_registry import WalletRegistryPort
from app.ports.api_key import ApiKeyPort
from app.ports.event_publisher import EventPublisherPort
from app.adapters.inmemory.link_token_repo import InMemoryLinkTokenRepository
from app.adapters.inmemory.audit import InMemoryAudit
from app.adapters.inmemory.user_repo import InMemoryUserRepository
from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistry
from app.adapters.inmemory.api_key_repo import InMemoryApiKeyRepository
from app.adapters.inmemory.event_publisher import InMemoryEventPublisher
from app.application.use_cases.create_link_token import CreateLinkTokenUseCase
from app.application.use_cases.bot_link import BotLinkUseCase, BotLinkService
from app.application.use_cases.register_wallet import RegisterWalletUseCase
from app.application.use_cases.get_user_status import GetUserStatusUseCase


def build_in_memory_services():
    """Build services with in-memory adapters for testing.

    Returns:
        Dictionary of services and use cases
    """
    # Create adapters
    link_token_port: LinkTokenPort = InMemoryLinkTokenRepository()
    audit_port: AuditPort = InMemoryAudit()
    user_repository_port: UserRepositoryPort = InMemoryUserRepository()
    wallet_registry_port: WalletRegistryPort = InMemoryWalletRegistry()
    api_key_port: ApiKeyPort = InMemoryApiKeyRepository()
    event_publisher_port: EventPublisherPort = InMemoryEventPublisher()

    # Create domain services
    policy_enforcer = PolicyEnforcer()
    link_token_service = LinkTokenService(
        link_token_port=link_token_port,
        audit_port=audit_port,
        policy_enforcer=policy_enforcer,
    )
    wallet_registry_service = WalletRegistryService(
        wallet_registry_port=wallet_registry_port,
        audit_port=audit_port,
    )
    bot_link_service = BotLinkService(
        link_token_service=link_token_service,
    )

    # Create use cases
    create_link_token_use_case = CreateLinkTokenUseCase(link_token_service=link_token_service)
    bot_link_use_case = BotLinkUseCase(bot_link_service=bot_link_service)
    register_wallet_use_case = RegisterWalletUseCase(
        wallet_registry_service=wallet_registry_service
    )
    get_user_status_use_case = GetUserStatusUseCase(user_repository=user_repository_port)

    return {
        "link_token_service": link_token_service,
        "wallet_registry_service": wallet_registry_service,
        "bot_link_service": bot_link_service,
        "create_link_token_use_case": create_link_token_use_case,
        "bot_link_use_case": bot_link_use_case,
        "register_wallet_use_case": register_wallet_use_case,
        "get_user_status_use_case": get_user_status_use_case,
        "link_token_port": link_token_port,
        "audit_port": audit_port,
        "user_repository_port": user_repository_port,
        "wallet_registry_port": wallet_registry_port,
        "api_key_port": api_key_port,
        "event_publisher_port": event_publisher_port,
        "policy_enforcer": policy_enforcer,
    }


def build_app():
    """Build application with in-memory adapters (for testing).

    Returns:
        Application services
    """
    return build_in_memory_services()


def build_app_components():
    """Build application components for dependency injection.

    Returns:
        Dictionary of application components
    """
    return build_in_memory_services()


def build_fastapi_app():
    """Build FastAPI app with wired dependencies.

    Returns:
        FastAPI application instance
    """
    from app.api.app import create_app

    components = build_app_components()
    return create_app(components)
