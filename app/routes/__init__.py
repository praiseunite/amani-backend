"""Routes module for API endpoints."""

from app.routes import health, auth, projects, milestones, escrow, wallet, payment

__all__ = ["health", "auth", "projects", "milestones", "escrow", "wallet", "payment"]
