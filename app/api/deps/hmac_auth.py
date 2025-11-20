"""HMAC authentication dependency for service-to-service auth."""

import hmac
import hashlib
import secrets
from typing import Optional
from datetime import datetime
from fastapi import Header, HTTPException, status

from app.ports.api_key import ApiKeyPort


class HMACAuth:
    """HMAC authentication handler."""

    def __init__(self, api_key_port: ApiKeyPort, time_window_seconds: int = 300):
        """Initialize HMAC auth.

        Args:
            api_key_port: Port for loading API key secrets
            time_window_seconds: Time window for timestamp validation (default 5 minutes)
        """
        self.api_key_port = api_key_port
        self.time_window_seconds = time_window_seconds

    async def verify(
        self,
        x_api_key_id: Optional[str] = Header(None),
        x_api_timestamp: Optional[str] = Header(None),
        x_api_signature: Optional[str] = Header(None),
    ) -> str:
        """Verify HMAC signature.

        Args:
            x_api_key_id: API key identifier from header
            x_api_timestamp: Timestamp from header
            x_api_signature: HMAC signature from header

        Returns:
            The API key ID if verification succeeds

        Raises:
            HTTPException: If verification fails
        """
        # Check required headers
        if not x_api_key_id or not x_api_timestamp or not x_api_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing HMAC authentication headers",
            )

        # Get secret for key ID
        secret = await self.api_key_port.get_secret(x_api_key_id)
        if secret is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        # Validate timestamp
        try:
            request_timestamp = int(x_api_timestamp)
            current_timestamp = int(datetime.utcnow().timestamp())

            time_diff = abs(current_timestamp - request_timestamp)
            if time_diff > self.time_window_seconds:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Request timestamp outside valid window",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid timestamp format",
            )

        # Calculate expected signature
        message = f"{x_api_key_id}:{x_api_timestamp}".encode("utf-8")
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            message,
            hashlib.sha256,
        ).hexdigest()

        # Compare signatures using constant-time comparison
        if not secrets.compare_digest(expected_signature, x_api_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

        return x_api_key_id


def create_hmac_auth_dependency(api_key_port: ApiKeyPort):
    """Create HMAC auth dependency.

    Args:
        api_key_port: Port for loading API key secrets

    Returns:
        HMAC auth dependency function
    """
    hmac_auth = HMACAuth(api_key_port)
    return hmac_auth.verify
