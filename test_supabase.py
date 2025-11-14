#!/usr/bin/env python3
"""
Test script to isolate Supabase client creation issue.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from supabase import create_client

# Import httpx after config
import httpx

# Monkey patch httpx to ignore proxy parameter
_original_init = httpx.Client.__init__

def patched_init(self, *args, **kwargs):
    # Remove proxy parameter if it exists
    kwargs.pop('proxy', None)
    return _original_init(self, *args, **kwargs)

httpx.Client.__init__ = patched_init

# Also patch AsyncClient
_original_async_init = httpx.AsyncClient.__init__

def patched_async_init(self, *args, **kwargs):
    # Remove proxy parameter if it exists
    kwargs.pop('proxy', None)
    return _original_async_init(self, *args, **kwargs)

httpx.AsyncClient.__init__ = patched_async_init

def test_supabase_client():
    """Test creating Supabase client."""
    try:
        print(f"Supabase URL: {settings.SUPABASE_URL}")
        print(f"Supabase Key: {settings.SUPABASE_KEY[:10]}...")

        # Try creating client
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        print("✅ Supabase client created successfully!")

        # Try auth
        auth = client.auth
        print("✅ Auth client accessible!")

        # Try magic link
        print("Testing magic link...")
        try:
            response = auth.sign_in_with_otp({
                "email": "test@example.com",
                "options": {}
            })
            print(f"✅ Magic link sent! Response: {response}")
        except Exception as e:
            print(f"❌ Magic link failed: {e}")
            import traceback
            traceback.print_exc()

        return True

    except Exception as e:
        print(f"❌ Error creating Supabase client: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_supabase_client()