"""Routes module for API endpoints."""

from app.routes import auth, escrow, health, milestones, payment, projects, wallet

__all__ = ["health", "auth", "projects", "milestones", "escrow", "wallet", "payment"]
