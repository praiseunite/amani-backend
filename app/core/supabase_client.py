"""
Supabase client configuration and utilities.
"""
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.
    
    Returns:
        Supabase client
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase credentials not configured. Magic link authentication will not work.")
            raise ValueError("Supabase credentials not configured")
        
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase client initialized")
    
    return _supabase_client


async def send_magic_link(email: str, redirect_url: Optional[str] = None) -> dict:
    """
    Send a magic link to user's email for passwordless authentication.
    
    Args:
        email: User's email address
        redirect_url: Optional URL to redirect after authentication
        
    Returns:
        Response from Supabase Auth
        
    Raises:
        Exception: If magic link sending fails
    """
    try:
        supabase = get_supabase_client()
        
        # Send magic link via Supabase Auth
        options = {}
        if redirect_url:
            options['redirect_to'] = redirect_url
        
        response = supabase.auth.sign_in_with_otp({
            'email': email,
            'options': options
        })
        
        logger.info(f"Magic link sent to {email}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to send magic link to {email}: {e}")
        raise


async def verify_magic_link_token(token: str) -> dict:
    """
    Verify a magic link token.
    
    Args:
        token: Magic link token from email
        
    Returns:
        User session data from Supabase
        
    Raises:
        Exception: If token verification fails
    """
    try:
        supabase = get_supabase_client()
        
        # Verify the token
        response = supabase.auth.verify_otp({
            'token': token,
            'type': 'magiclink'
        })
        
        logger.info(f"Magic link verified successfully")
        return response
        
    except Exception as e:
        logger.error(f"Failed to verify magic link token: {e}")
        raise
