"""
FinCra API client for payment processing.
Handles async calls, retries, and error handling.
"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from decimal import Decimal

from app.core.config import settings


logger = logging.getLogger(__name__)


class FinCraError(Exception):
    """Base exception for FinCra API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class FinCraClient:
    """
    Async client for FinCra payment API.
    Includes retry logic and comprehensive error handling.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0
    ):
        """
        Initialize FinCra API client.
        
        Args:
            api_key: FinCra API key
            api_secret: FinCra API secret
            base_url: FinCra API base URL
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.FINCRA_API_KEY
        self.api_secret = api_secret or settings.FINCRA_API_SECRET
        self.base_url = base_url or settings.FINCRA_BASE_URL
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        if not self.api_key or not self.api_secret:
            logger.warning("FinCra API credentials not configured")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "api-key": self.api_key,
            }
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
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to FinCra API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt
            
        Returns:
            Response data as dictionary
            
        Raises:
            FinCraError: If request fails after all retries
        """
        try:
            logger.info(f"FinCra API request: {method} {endpoint} (attempt {retry_count + 1}/{self.max_retries + 1})")
            
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params
            )
            
            # Log response
            logger.info(f"FinCra API response: {response.status_code}")
            
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
                wait_time = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                logger.warning(
                    f"FinCra API error {response.status_code}, retrying in {wait_time}s... "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            # Raise error if not retryable or max retries reached
            error_message = error_data.get("message", "Unknown error")
            logger.error(f"FinCra API error: {response.status_code} - {error_message}")
            raise FinCraError(
                message=f"FinCra API error: {error_message}",
                status_code=response.status_code,
                response_data=error_data
            )
        
        except httpx.TimeoutException as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"FinCra API timeout, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            logger.error(f"FinCra API timeout after {retry_count + 1} attempts")
            raise FinCraError(message="Request timeout", status_code=None, response_data=None)
        
        except httpx.RequestError as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"FinCra API request error: {e}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            logger.error(f"FinCra API request error: {e}")
            raise FinCraError(message=f"Request error: {str(e)}", status_code=None, response_data=None)
    
    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        customer_email: str,
        reference: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment transaction.
        
        Args:
            amount: Payment amount
            currency: Currency code (e.g., "USD")
            customer_email: Customer's email
            reference: Unique reference for the transaction
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            Payment response data
        """
        data = {
            "amount": str(amount),
            "currency": currency,
            "customer": {
                "email": customer_email
            },
            "reference": reference,
            "description": description or f"Payment for {reference}",
            "metadata": metadata or {}
        }
        
        return await self._make_request("POST", "/payments", data=data)
    
    async def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify a payment transaction status.
        
        Args:
            transaction_id: FinCra transaction ID
            
        Returns:
            Payment verification data
        """
        return await self._make_request("GET", f"/payments/{transaction_id}")
    
    async def create_transfer(
        self,
        amount: Decimal,
        currency: str,
        recipient_account: str,
        recipient_bank_code: str,
        reference: str,
        narration: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a transfer/payout transaction.
        
        Args:
            amount: Transfer amount
            currency: Currency code
            recipient_account: Recipient's account number
            recipient_bank_code: Recipient's bank code
            reference: Unique reference for the transaction
            narration: Transfer narration
            metadata: Additional metadata
            
        Returns:
            Transfer response data
        """
        data = {
            "amount": str(amount),
            "currency": currency,
            "beneficiary": {
                "accountNumber": recipient_account,
                "bankCode": recipient_bank_code
            },
            "reference": reference,
            "narration": narration or f"Transfer for {reference}",
            "metadata": metadata or {}
        }
        
        return await self._make_request("POST", "/transfers", data=data)
    
    async def verify_transfer(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify a transfer transaction status.
        
        Args:
            transaction_id: FinCra transaction ID
            
        Returns:
            Transfer verification data
        """
        return await self._make_request("GET", f"/transfers/{transaction_id}")
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account balance.
        
        Args:
            currency: Optional currency filter
            
        Returns:
            Balance information
        """
        params = {"currency": currency} if currency else None
        return await self._make_request("GET", "/balance", params=params)


# Global client instance (will be initialized on app startup)
fincra_client: Optional[FinCraClient] = None


def get_fincra_client() -> FinCraClient:
    """
    Get the global FinCra client instance.
    
    Returns:
        FinCra client instance
        
    Raises:
        ValueError: If client is not initialized
    """
    global fincra_client
    
    if fincra_client is None:
        fincra_client = FinCraClient()
    
    return fincra_client
