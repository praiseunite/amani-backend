"""
LNbits API client for Lightning Network payment processing.
Handles async calls, retries, and error handling.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LNbitsError(Exception):
    """Base exception for LNbits API errors."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class LNbitsClient:
    """
    Async client for LNbits Lightning API.
    Includes retry logic and comprehensive error handling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
    ):
        """
        Initialize LNbits API client.

        Args:
            api_key: LNbits API key (admin or invoice key)
            base_url: LNbits instance base URL
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.LNBITS_API_KEY
        self.base_url = base_url or settings.LNBITS_BASE_URL
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        if not self.api_key:
            logger.warning("LNbits API key not configured")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key,
            },
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to LNbits API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            Response data as dictionary

        Raises:
            LNbitsError: If request fails after all retries
        """
        try:
            logger.info(
                f"LNbits API request: {method} {endpoint} (attempt {retry_count + 1}/{self.max_retries + 1})"
            )

            response = await self.client.request(
                method=method, url=endpoint, json=data, params=params
            )

            # Log response
            logger.info(f"LNbits API response: {response.status_code}")

            # Check for success
            if response.status_code in (200, 201):
                response_data = response.json()
                return response_data

            # Handle errors
            error_data = None
            try:
                error_data = response.json()
            except Exception:
                error_data = {"message": response.text}

            # Retry on server errors (5xx) or rate limiting (429)
            if response.status_code in (429, 500, 502, 503, 504) and retry_count < self.max_retries:
                wait_time = self.retry_delay * (2**retry_count)  # Exponential backoff
                logger.warning(
                    f"LNbits API error {response.status_code}, retrying in {wait_time}s... "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)

            # Raise error if not retryable or max retries reached
            error_message = error_data.get("detail") or error_data.get("message", "Unknown error")
            logger.error(f"LNbits API error: {response.status_code} - {error_message}")
            raise LNbitsError(
                message=f"LNbits API error: {error_message}",
                status_code=response.status_code,
                response_data=error_data,
            )

        except httpx.TimeoutException as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2**retry_count)
                logger.warning(f"LNbits API timeout, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)

            logger.error(f"LNbits API timeout after {retry_count + 1} attempts")
            raise LNbitsError(message="Request timeout", status_code=None, response_data=None)

        except httpx.RequestError as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2**retry_count)
                logger.warning(f"LNbits API request error: {e}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)

            logger.error(f"LNbits API request error: {e}")
            raise LNbitsError(
                message=f"Request error: {str(e)}", status_code=None, response_data=None
            )

    async def create_wallet(
        self,
        user_name: str,
        wallet_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Lightning wallet.

        Args:
            user_name: User identifier/name
            wallet_name: Optional wallet name

        Returns:
            Wallet creation response with ID and keys
        """
        data = {
            "name": wallet_name or f"{user_name}_wallet",
            "user_name": user_name,
        }

        return await self._make_request("POST", "/api/v1/wallet", data=data)

    async def get_wallet_details(self) -> Dict[str, Any]:
        """
        Get wallet details including balance.
        
        Uses the API key from headers to identify the wallet.

        Returns:
            Wallet details with balance
        """
        return await self._make_request("GET", "/api/v1/wallet")

    async def create_invoice(
        self,
        amount: int,
        memo: Optional[str] = None,
        unit: str = "sat",
        expiry: Optional[int] = None,
        webhook: Optional[str] = None,
        out: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Lightning invoice (payment request).

        Args:
            amount: Invoice amount in satoshis
            memo: Invoice description/memo
            unit: Unit for amount (sat or msat)
            expiry: Invoice expiry in seconds
            webhook: Webhook URL for payment notification
            out: If True, creates a payment (outgoing), otherwise invoice (incoming)

        Returns:
            Invoice data with payment_hash and payment_request
        """
        data = {
            "amount": amount,
            "memo": memo or "Payment",
            "unit": unit,
            "out": out,
        }

        if expiry:
            data["expiry"] = expiry
        if webhook:
            data["webhook"] = webhook

        return await self._make_request("POST", "/api/v1/payments", data=data)

    async def check_invoice(self, payment_hash: str) -> Dict[str, Any]:
        """
        Check invoice/payment status.

        Args:
            payment_hash: Payment hash from invoice

        Returns:
            Payment status and details
        """
        return await self._make_request("GET", f"/api/v1/payments/{payment_hash}")

    async def decode_invoice(self, payment_request: str) -> Dict[str, Any]:
        """
        Decode a Lightning invoice (BOLT11).

        Args:
            payment_request: BOLT11 payment request string

        Returns:
            Decoded invoice data
        """
        data = {"data": payment_request}
        return await self._make_request("POST", "/api/v1/payments/decode", data=data)

    async def pay_invoice(
        self,
        bolt11: str,
        out: bool = True,
    ) -> Dict[str, Any]:
        """
        Pay a Lightning invoice.

        Args:
            bolt11: BOLT11 payment request
            out: Must be True for outgoing payment

        Returns:
            Payment result
        """
        data = {
            "out": out,
            "bolt11": bolt11,
        }

        return await self._make_request("POST", "/api/v1/payments", data=data)

    async def get_balance(self) -> Dict[str, Any]:
        """
        Get wallet balance.

        Returns:
            Balance information in msats
        """
        wallet_details = await self.get_wallet_details()
        return {
            "balance": wallet_details.get("balance", 0),
            "currency": "msat",
        }


# Global client instance (will be initialized on app startup)
lnbits_client: Optional[LNbitsClient] = None


def get_lnbits_client() -> LNbitsClient:
    """
    Get the global LNbits client instance.

    Returns:
        LNbits client instance

    Raises:
        ValueError: If client is not initialized
    """
    global lnbits_client

    if lnbits_client is None:
        lnbits_client = LNbitsClient()

    return lnbits_client
