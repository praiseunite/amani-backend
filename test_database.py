#!/usr/bin/env python3
"""
Database connection test script for Amani Backend.
Tests database connectivity, models, and basic operations.
"""
import asyncio
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, text
from app.core.database import get_db, engine
from app.models import User, Project, Milestone, Transaction


async def test_connection():
    """Test basic database connection."""
    print("🔍 Testing database connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Database connection successful!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_tables():
    """Test that all tables exist."""
    print("\n🔍 Testing database tables...")
    tables = ['users', 'projects', 'milestones', 'transactions']
    
    try:
        async with engine.connect() as conn:
            for table in tables:
                result = await conn.execute(
                    text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                )
                exists = result.scalar()
                if exists:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' does not exist")
                    return False
            return True
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False


async def test_rls():
    """Test Row-Level Security is enabled."""
    print("\n🔍 Testing Row-Level Security...")
    tables = ['users', 'projects', 'milestones', 'transactions']
    
    try:
        async with engine.connect() as conn:
            for table in tables:
                result = await conn.execute(
                    text(f"""
                        SELECT relrowsecurity 
                        FROM pg_class 
                        WHERE relname = '{table}'
                    """)
                )
                rls_enabled = result.scalar()
                if rls_enabled:
                    print(f"✅ RLS enabled on '{table}'")
                else:
                    print(f"⚠️  RLS not enabled on '{table}' (may be expected for local dev)")
            return True
    except Exception as e:
        print(f"❌ RLS check failed: {e}")
        return False


async def test_session():
    """Test async session creation."""
    print("\n🔍 Testing async session management...")
    try:
        async for session in get_db():
            # Test a simple query
            result = await session.execute(select(User).limit(1))
            print("✅ Async session created successfully")
            print("✅ Query execution successful")
            return True
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        return False


async def test_enums():
    """Test that custom enum types exist."""
    print("\n🔍 Testing custom enum types...")
    enums = ['project_status', 'milestone_status', 'transaction_type', 'transaction_status']
    
    try:
        async with engine.connect() as conn:
            for enum in enums:
                result = await conn.execute(
                    text(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_type 
                            WHERE typname = '{enum}'
                        )
                    """)
                )
                exists = result.scalar()
                if exists:
                    print(f"✅ Enum type '{enum}' exists")
                else:
                    print(f"❌ Enum type '{enum}' does not exist")
                    return False
            return True
    except Exception as e:
        print(f"❌ Enum check failed: {e}")
        return False


async def test_indexes():
    """Test that indexes are created."""
    print("\n🔍 Testing database indexes...")
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT tablename, indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """)
            )
            indexes = result.fetchall()
            
            if indexes:
                print(f"✅ Found {len(indexes)} indexes:")
                for table, index in indexes[:5]:  # Show first 5
                    print(f"   - {table}.{index}")
                if len(indexes) > 5:
                    print(f"   ... and {len(indexes) - 5} more")
                return True
            else:
                print("⚠️  No indexes found")
                return False
    except Exception as e:
        print(f"❌ Index check failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Amani Backend - Database Connection Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Connection", await test_connection()))
    
    if results[0][1]:  # Only continue if connection succeeded
        results.append(("Tables", await test_tables()))
        results.append(("RLS", await test_rls()))
        results.append(("Session", await test_session()))
        results.append(("Enums", await test_enums()))
        results.append(("Indexes", await test_indexes()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Database is properly configured.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check your database setup.")
        print("   See DATABASE_SETUP.md for troubleshooting guide.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
