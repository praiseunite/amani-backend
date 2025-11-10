# Database Setup Guide

Complete guide for setting up the database with Supabase PostgreSQL for the Amani Backend.

## Table of Contents
1. [Database Architecture](#database-architecture)
2. [Local Development Setup](#local-development-setup)
3. [Supabase Setup](#supabase-setup)
4. [Running Migrations](#running-migrations)
5. [Testing Database Connection](#testing-database-connection)
6. [Common Operations](#common-operations)

## Database Architecture

### Models

#### User Model (`app/models/user.py`)
User authentication and profile management.

**Fields:**
- `id`: UUID primary key
- `email`: Unique email address
- `full_name`: User's full name
- `phone_number`: Contact number
- `hashed_password`: Encrypted password (if not using Supabase Auth)
- `is_active`, `is_verified`, `is_superuser`: Status flags
- `avatar_url`, `bio`: Profile information
- `created_at`, `updated_at`, `last_login`: Timestamps

**Relationships:**
- One-to-many with Projects (as creator, buyer, seller)
- One-to-many with Transactions

#### Project Model (`app/models/project.py`)
Escrow project/agreement tracking.

**Fields:**
- `id`: UUID primary key
- `title`, `description`: Project details
- `total_amount`, `currency`: Financial information
- `status`: Enum (draft, pending, active, in_progress, completed, disputed, cancelled, refunded)
- `creator_id`, `buyer_id`, `seller_id`: Foreign keys to User
- `terms_accepted_at`: Terms acceptance timestamp
- `completion_criteria`: Project completion requirements
- `start_date`, `due_date`, `completed_at`: Timeline
- `created_at`, `updated_at`: Timestamps

**Relationships:**
- Many-to-one with User (creator, buyer, seller)
- One-to-many with Milestones
- One-to-many with Transactions

#### Milestone Model (`app/models/milestone.py`)
Project deliverable tracking.

**Fields:**
- `id`: UUID primary key
- `project_id`: Foreign key to Project
- `title`, `description`: Milestone details
- `order_index`: Ordering within project
- `amount`, `currency`: Payment amount
- `status`: Enum (pending, in_progress, completed, approved, rejected, disputed)
- `is_paid`: Payment status flag
- `completion_criteria`, `completion_notes`: Completion information
- `due_date`, `completed_at`, `approved_at`, `paid_at`: Timeline
- `created_at`, `updated_at`: Timestamps

**Relationships:**
- Many-to-one with Project

#### Transaction Model (`app/models/transaction.py`)
Financial transaction tracking.

**Fields:**
- `id`: UUID primary key
- `user_id`, `project_id`: Foreign keys
- `transaction_type`: Enum (deposit, withdrawal, escrow_hold, escrow_release, refund, fee, commission)
- `status`: Enum (pending, processing, completed, failed, cancelled, refunded)
- `amount`, `currency`, `fee`, `net_amount`: Financial information
- `payment_gateway`: Gateway name (default: fincra)
- `gateway_transaction_id`, `gateway_reference`, `gateway_response`: Gateway integration
- `description`, `notes`, `extra_data`: Additional information
- `created_at`, `updated_at`, `processed_at`, `completed_at`: Timestamps

**Relationships:**
- Many-to-one with User
- Many-to-one with Project

## Local Development Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS (with Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE amani_dev;
CREATE USER amani_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE amani_dev TO amani_user;

# Enable UUID extension
\c amani_dev
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Exit
\q
```

### 3. Configure Environment

Update your `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://amani_user:your_password@localhost:5432/amani_dev
```

### 4. Run Migrations

```bash
# Apply all migrations
alembic upgrade head

# Verify
alembic current
```

## Supabase Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com/)
2. Create a new project
3. Choose a region close to your users
4. Set a strong database password

### 2. Get Connection Details

From your Supabase project dashboard:

1. Go to **Settings** → **Database**
2. Copy the connection string (choose "URI" format)
3. Replace `postgresql://` with `postgresql+asyncpg://`

### 3. Get API Keys

From your Supabase project dashboard:

1. Go to **Settings** → **API**
2. Copy:
   - Project URL (SUPABASE_URL)
   - `anon` `public` key (SUPABASE_KEY)
   - `service_role` key (SUPABASE_SERVICE_KEY)

### 4. Configure Environment

Update your `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 5. Enable Extensions

In Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 6. Run Migrations

```bash
alembic upgrade head
```

### 7. Verify Row-Level Security

In Supabase SQL Editor:
```sql
-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- View policies
SELECT * FROM pg_policies;
```

## Running Migrations

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Apply to specific revision
alembic upgrade <revision>
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to base (WARNING: removes all tables)
alembic downgrade base

# Rollback to specific revision
alembic downgrade <revision>
```

### Check Status

```bash
# Current version
alembic current

# Migration history
alembic history

# Check for pending migrations
alembic current
alembic heads
```

## Testing Database Connection

### 1. Create Test Script

Create `test_db.py`:
```python
import asyncio
from app.core.database import get_db, engine
from app.models import User
from sqlalchemy import select

async def test_connection():
    """Test database connection."""
    try:
        # Test connection
        async with engine.connect() as conn:
            print("✅ Database connection successful!")
        
        # Test session
        async for session in get_db():
            # Test query
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            print(f"✅ Database query successful! User count: {0 if user is None else 1}")
            break
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

### 2. Run Test

```bash
python test_db.py
```

### 3. Test Async Session

Create `test_crud.py`:
```python
import asyncio
import uuid
from app.core.database import get_db
from app.models import User

async def test_crud():
    """Test CRUD operations."""
    async for session in get_db():
        # Create
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            full_name="Test User",
            is_active=True
        )
        session.add(user)
        await session.commit()
        print(f"✅ User created: {user.email}")
        
        # Read
        await session.refresh(user)
        print(f"✅ User read: {user.full_name}")
        
        # Update
        user.full_name = "Updated User"
        await session.commit()
        print(f"✅ User updated: {user.full_name}")
        
        # Delete
        await session.delete(user)
        await session.commit()
        print("✅ User deleted")
        
        break

if __name__ == "__main__":
    asyncio.run(test_crud())
```

## Common Operations

### Create Admin User

```python
import asyncio
import uuid
from app.core.database import get_db
from app.models import User
from app.core.security import get_password_hash

async def create_admin():
    async for session in get_db():
        admin = User(
            id=uuid.uuid4(),
            email="admin@amani.com",
            full_name="Admin User",
            hashed_password=get_password_hash("secure_password"),
            is_active=True,
            is_verified=True,
            is_superuser=True
        )
        session.add(admin)
        await session.commit()
        print(f"✅ Admin created: {admin.email}")
        break

asyncio.run(create_admin())
```

### Query with Relationships

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Eager load relationships
stmt = select(User).options(
    selectinload(User.projects_created),
    selectinload(User.transactions)
).where(User.email == "user@example.com")

result = await session.execute(stmt)
user = result.scalar_one()
```

### Transaction Example

```python
async with session.begin():
    # All operations in this block are part of one transaction
    user = User(...)
    session.add(user)
    
    project = Project(creator_id=user.id, ...)
    session.add(project)
    
    # Automatic commit if no exception
    # Automatic rollback if exception occurs
```

## Troubleshooting

### Common Issues

#### 1. Connection Timeout
**Problem:** Database connection times out

**Solution:**
- Check if PostgreSQL is running
- Verify firewall rules
- For Supabase, check if your IP is allowed
- Try using connection pooling

#### 2. RLS Blocking Queries
**Problem:** Queries return no results even though data exists

**Solution:**
- Check if RLS policies are correct
- Ensure `auth.uid()` is properly set
- Use service role key for admin operations
- Temporarily disable RLS for testing:
  ```sql
  ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
  ```

#### 3. Migration Conflicts
**Problem:** Migration version mismatch

**Solution:**
```bash
# Check current state
alembic current
alembic heads

# Stamp database with current version
alembic stamp head

# Or downgrade and re-upgrade
alembic downgrade base
alembic upgrade head
```

#### 4. AsyncPG Import Error
**Problem:** `asyncpg` module not found

**Solution:**
```bash
pip install asyncpg==0.29.0
```

### Performance Tips

1. **Use Indexes:** Already added to frequently queried columns
2. **Connection Pooling:** Configured in `app/core/database.py`
3. **Eager Loading:** Use `selectinload()` for relationships
4. **Batch Operations:** Use `bulk_insert_mappings()` for multiple inserts
5. **Query Optimization:** Use `explain()` to analyze query performance

## Security Best Practices

1. **Never commit** `.env` file with real credentials
2. **Rotate keys** regularly, especially service role keys
3. **Use RLS** policies in production
4. **Encrypt sensitive data** at rest
5. **Use prepared statements** (SQLAlchemy does this automatically)
6. **Monitor access logs** for suspicious activity
7. **Keep dependencies updated** for security patches

## Next Steps

After setting up the database:

1. ✅ Database models and migrations are complete
2. ✅ Async session management is configured
3. ✅ Row-Level Security is implemented
4. 📝 Create Pydantic schemas in `app/schemas/`
5. 📝 Implement CRUD operations in `app/crud/`
6. 📝 Add API endpoints in `app/routes/`
7. 📝 Add authentication and authorization
8. 📝 Integrate with FinCra payment API
9. 📝 Add comprehensive tests

## Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Supabase Documentation](https://supabase.com/docs)
- [AsyncPG Documentation](https://magicstack.github.io/asyncpg/)
- [FastAPI Database Guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)
