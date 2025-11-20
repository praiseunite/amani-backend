#!/usr/bin/env python3
"""
Run script for the Amani Backend - Hexagonal Architecture API.
This script starts the new FastAPI application with wired dependencies.
"""
import os
import sys

# Ensure we're in the project directory
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Import after setting up the environment
try:
    import uvicorn
    from app.composition import build_fastapi_app
except ImportError as e:
    print("❌ Error: Required dependencies not installed")
    print("📦 Please install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print(f"Error details: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Amani Backend - Hexagonal Architecture API...")
    print("📍 Environment: development")
    print("🌐 Server: http://127.0.0.1:8001")
    print("📚 API Docs: http://127.0.0.1:8001/docs")
    print()
    print("Available endpoints:")
    print("  POST   /api/v1/link_tokens/create")
    print("  POST   /api/v1/bot/link (HMAC auth)")
    print("  POST   /api/v1/wallets/register (HMAC auth)")
    print("  GET    /api/v1/users/{id}/status")
    print()

    # Build the FastAPI app with wired dependencies
    app = build_fastapi_app()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
