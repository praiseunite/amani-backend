"""
Request ID middleware for distributed tracing and log correlation.
"""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates or extracts a unique request ID for each request.
    
    The request ID can be used for:
    - Distributed tracing
    - Log correlation
    - Request tracking across services
    """

    REQUEST_ID_HEADER = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and ensure it has a request ID.
        
        If the request already has an X-Request-ID header, use it.
        Otherwise, generate a new UUID.
        """
        # Check if request already has an ID
        request_id = request.headers.get(self.REQUEST_ID_HEADER)
        
        # Generate new ID if not present
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state for access in route handlers
        request.state.request_id = request_id
        
        # Call the next middleware/route handler
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[self.REQUEST_ID_HEADER] = request_id
        
        return response


def get_request_id(request: Request) -> str:
    """
    Helper function to get the request ID from a request object.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        The request ID string
    """
    return getattr(request.state, "request_id", "unknown")
