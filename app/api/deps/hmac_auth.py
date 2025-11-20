"""HMAC authentication dependency."""

import hmac
import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import Header, HTTPException, Request
from fastapi.security import HTTPBearer

from app.ports.api_key import ApiKeyPort


# HMAC auth scheme for documentation
hmac_scheme = HTTPBearer(
    scheme_name="HMAC Authentication",
    description="Requires X-API-KEY-ID, X-API-TIMESTAMP, and X-API-SIGNATURE headers",
)


class HMACAuth:
    """HMAC authentication dependency."""

    def __init__(self, api_key_port: ApiKeyPort, time_window_seconds: int = 300):
        """Initialize HMAC auth.

        Args:
            api_key_port: Port to fetch API key secrets
            time_window_seconds: Time window for timestamp validation (default 5 minutes)
        """
        self.api_key_port = api_key_port
        self.time_window_seconds = time_window_seconds

    async def __call__(
        self,
        request: Request,
        x_api_key_id: Optional[str] = Header(None, alias="X-API-KEY-ID"),
        x_api_timestamp: Optional[str] = Header(None, alias="X-API-TIMESTAMP"),
        x_api_signature: Optional[str] = Header(None, alias="X-API-SIGNATURE"),
    ) -> str:
        """Verify HMAC signature.

        Args:
            request: FastAPI request object
            x_api_key_id: API key ID from header
            x_api_timestamp: Timestamp from header
            x_api_signature: HMAC signature from header

        Returns:
            The verified API key ID

        Raises:
            HTTPException: If authentication fails
        """
        # Check all required headers are present
        if not x_api_key_id or not x_api_timestamp or not x_api_signature:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Missing required HMAC headers: "
                    "X-API-KEY-ID, X-API-TIMESTAMP, X-API-SIGNATURE"
                ),
            )

        # Validate timestamp
        try:
            timestamp = int(x_api_timestamp)
            current_time = int(datetime.utcnow().timestamp())

            if abs(current_time - timestamp) > self.time_window_seconds:
                raise HTTPException(
                    status_code=401, detail="Request timestamp outside valid time window"
                )
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid timestamp format")

        # Get API key secret
        secret = await self.api_key_port.get_secret_by_key_id(x_api_key_id)
        if not secret:
            raise HTTPException(status_code=401, detail="Invalid API key ID")

        # Read request body
        body = await request.body()

        # Construct message to sign: METHOD + PATH + TIMESTAMP + BODY
        message = f"{request.method}{request.url.path}{x_api_timestamp}{body.decode('utf-8')}"

        # Compute expected signature
        expected_signature = hmac.new(
            secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Compare signatures using constant-time comparison
        if not secrets.compare_digest(expected_signature, x_api_signature):
            raise HTTPException(status_code=401, detail="Invalid HMAC signature")

        return x_api_key_id


def create_hmac_auth(api_key_port: ApiKeyPort) -> HMACAuth:
    """Create HMAC auth dependency.

    Args:
        api_key_port: Port to fetch API key secrets

    Returns:
        HMAC auth dependency
    """
    return HMACAuth(api_key_port=api_key_port)
