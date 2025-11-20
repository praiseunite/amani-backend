"""FastAPI app factory."""

from typing import Dict, Any

from fastapi import FastAPI

from app.api.controllers.link_tokens import create_link_tokens_router
from app.api.controllers.bot_link import create_bot_link_router
from app.api.controllers.wallets import create_wallets_router
from app.api.controllers.users import create_users_router
from app.api.deps.hmac_auth import create_hmac_auth
from app.composition import build_app_components


def build_fastapi_app(components: Dict[str, Any] = None) -> FastAPI:
    """Build FastAPI application with dependency injection.

    Args:
        components: Optional pre-built components dictionary.
                   If None, will call build_app_components()

    Returns:
        Configured FastAPI application
    """
    # Build components if not provided
    if components is None:
        components = build_app_components()

    # Create FastAPI app
    app = FastAPI(
        title="Amani Backend API",
        description="Hexagonal architecture backend with FastAPI",
        version="1.0.0",
    )

    # Create HMAC auth dependency
    hmac_auth = create_hmac_auth(components["api_key_port"])

    # Create routers with dependencies
    link_tokens_router = create_link_tokens_router(components["create_link_token_use_case"])
    bot_link_router = create_bot_link_router(components["consume_link_token_use_case"], hmac_auth)
    wallets_router = create_wallets_router(components["register_wallet_use_case"], hmac_auth)
    users_router = create_users_router(components["get_user_status_use_case"])

    # Include routers
    app.include_router(link_tokens_router, prefix="/api/v1")
    app.include_router(bot_link_router, prefix="/api/v1")
    app.include_router(wallets_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app
