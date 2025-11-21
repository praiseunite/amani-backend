"""FastAPI app factory - wires routers and middleware."""

from fastapi import FastAPI

from app.api.controllers.link_tokens import create_link_tokens_router
from app.api.controllers.bot_link import create_bot_link_router
from app.api.controllers.wallets import create_wallets_router
from app.api.controllers.users import create_users_router
from app.api.controllers.events_admin import create_events_admin_router
from app.api.controllers.wallet_events import create_wallet_events_router
from app.api.deps.hmac_auth import create_hmac_auth_dependency


def create_app(components: dict) -> FastAPI:
    """Create FastAPI application with wired dependencies.

    Args:
        components: Dictionary of application components (use cases, ports, etc.)

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Amani Backend API",
        version="1.0.0",
        description="Hexagonal architecture backend with HMAC auth",
    )

    # Create HMAC auth dependency
    hmac_auth_dependency = create_hmac_auth_dependency(components["api_key_port"])

    # Create routers with dependencies
    link_tokens_router = create_link_tokens_router(components["create_link_token_use_case"])
    bot_link_router = create_bot_link_router(
        components["bot_link_use_case"],
        hmac_auth_dependency,
    )
    wallets_router = create_wallets_router(
        components["register_wallet_use_case"],
        hmac_auth_dependency,
    )
    users_router = create_users_router(
        components["get_user_status_use_case"],
        hmac_auth_dependency,
    )
    events_admin_router = create_events_admin_router(components["event_publisher_port"])
    wallet_events_router = create_wallet_events_router(
        components["ingest_wallet_event_use_case"],
        components["list_wallet_events_use_case"],
        hmac_auth_dependency,
    )

    # Include routers
    app.include_router(link_tokens_router, prefix="/api/v1")
    app.include_router(bot_link_router, prefix="/api/v1")
    app.include_router(wallets_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(events_admin_router, prefix="/api/v1")
    app.include_router(wallet_events_router, prefix="/api/v1")

    return app
