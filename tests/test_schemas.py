"""
Tests for project schemas validation.
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.models.project import ProjectStatus


class TestProjectSchemas:
    """Test project schema validation."""

    def test_project_create_valid(self):
        """Test valid project creation data."""
        data = {
            "title": "Test Project",
            "description": "This is a test project description",
            "total_amount": Decimal("1000.00"),
            "currency": "USD",
            "due_date": datetime.utcnow() + timedelta(days=30),
        }

        project = ProjectCreate(**data)

        assert project.title == "Test Project"
        assert project.total_amount == Decimal("1000.00")
        assert project.currency == "USD"

    def test_project_create_with_buyer_seller(self):
        """Test project creation with buyer and seller IDs."""
        buyer_id = uuid4()
        seller_id = uuid4()

        data = {
            "title": "Test Project",
            "description": "This is a test project",
            "total_amount": Decimal("1000.00"),
            "buyer_id": buyer_id,
            "seller_id": seller_id,
        }

        project = ProjectCreate(**data)

        assert project.buyer_id == buyer_id
        assert project.seller_id == seller_id

    def test_project_create_title_too_short(self):
        """Test project creation with title too short."""
        data = {
            "title": "AB",  # Less than 3 characters
            "description": "This is a test project",
            "total_amount": Decimal("1000.00"),
        }

        with pytest.raises(ValidationError):
            ProjectCreate(**data)

    def test_project_create_description_too_short(self):
        """Test project creation with description too short."""
        data = {
            "title": "Test Project",
            "description": "Short",  # Less than 10 characters
            "total_amount": Decimal("1000.00"),
        }

        with pytest.raises(ValidationError):
            ProjectCreate(**data)

    def test_project_create_negative_amount(self):
        """Test project creation with negative amount."""
        data = {
            "title": "Test Project",
            "description": "This is a test project",
            "total_amount": Decimal("-100.00"),
        }

        with pytest.raises(ValidationError):
            ProjectCreate(**data)

    def test_project_create_zero_amount(self):
        """Test project creation with zero amount."""
        data = {
            "title": "Test Project",
            "description": "This is a test project",
            "total_amount": Decimal("0.00"),
        }

        with pytest.raises(ValidationError):
            ProjectCreate(**data)

    def test_project_create_invalid_currency(self):
        """Test project creation with invalid currency code."""
        data = {
            "title": "Test Project",
            "description": "This is a test project",
            "total_amount": Decimal("1000.00"),
            "currency": "USDD",  # Invalid, should be 3 characters
        }

        with pytest.raises(ValidationError):
            ProjectCreate(**data)

    def test_project_update_partial(self):
        """Test partial project update."""
        data = {"title": "Updated Title"}

        update = ProjectUpdate(**data)

        assert update.title == "Updated Title"
        assert update.description is None
        assert update.total_amount is None

    def test_project_update_status(self):
        """Test updating project status."""
        data = {"status": ProjectStatus.ACTIVE}

        update = ProjectUpdate(**data)

        assert update.status == ProjectStatus.ACTIVE
