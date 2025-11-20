"""Tests for user status API endpoint."""

from uuid import uuid4


class TestUsersStatusAPI:
    """Test cases for user status endpoint."""

    def test_get_user_status_success(self, client, test_user):
        """Test getting user status successfully."""
        response = client.get(f"/api/v1/users/{test_user.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role
        assert data["is_active"] == test_user.is_active
        assert data["is_verified"] == test_user.is_verified

    def test_get_user_status_not_found(self, client):
        """Test getting status for non-existent user."""
        non_existent_id = uuid4()
        response = client.get(f"/api/v1/users/{non_existent_id}/status")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_status_invalid_uuid(self, client):
        """Test getting status with invalid UUID format."""
        response = client.get("/api/v1/users/not-a-uuid/status")

        assert response.status_code == 422  # Validation error

    def test_get_user_status_multiple_users(self, client, components):
        """Test getting status for multiple users."""
        # Create multiple test users
        users = []
        for i in range(3):
            from app.domain.entities import User

            user = User(
                id=uuid4(),
                email=f"test{i}@example.com",
                full_name=f"Test User {i}",
                role="client",
                is_active=True,
                is_verified=i % 2 == 0,  # Alternate verification status
            )
            import asyncio

            asyncio.run(components["user_repository_port"].save(user))
            users.append(user)

        # Verify each user's status
        for user in users:
            response = client.get(f"/api/v1/users/{user.id}/status")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(user.id)
            assert data["email"] == user.email
            assert data["is_verified"] == user.is_verified
