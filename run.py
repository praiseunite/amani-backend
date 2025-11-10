#!/usr/bin/env python3
"""
Run script for the Amani Escrow Backend.
This script starts the FastAPI application with Uvicorn.
"""
import os
import sys

# Ensure we're in the project directory
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Check if .env file exists
if not os.path.exists('.env'):
    print("⚠️  Warning: .env file not found!")
    print("📝 Please create a .env file from .env.example:")
    print("   cp .env.example .env")
    print("   # Then edit .env with your actual configuration")
    print()
    response = input("Continue anyway? (y/N): ")
    if response.lower() != 'y':
        sys.exit(1)

# Import after setting up the environment
try:
    import uvicorn
    from app.core.config import settings
except ImportError as e:
    print("❌ Error: Required dependencies not installed")
    print("📦 Please install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print(f"Error details: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Amani Escrow Backend...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
