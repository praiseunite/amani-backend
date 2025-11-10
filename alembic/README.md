# Database Migrations

This directory contains Alembic database migrations for the Amani Backend.

## Overview

The migrations are configured to work with:
- **PostgreSQL** with async SQLAlchemy
- **Supabase** for hosted PostgreSQL with Row-Level Security
- **asyncpg** as the database driver

## Migration Files

### Initial Migrations

1. **68db6a7fba94_initial_migration_with_user_project_.py**
   - Creates all base tables: `users`, `projects`, `milestones`, `transactions`
   - Sets up relationships and foreign keys
   - Creates custom PostgreSQL enum types
   - Adds indexes for performance

2. **65ed9294ba55_add_row_level_security_policies.py**
   - Enables Row-Level Security (RLS) on all tables
   - Creates policies for Supabase auth integration
   - Ensures users can only access their own data
   - Protects sensitive operations

## Database Schema

### Tables

#### Users
- Primary table for user authentication and profiles
- Integrates with Supabase Auth
- Fields: email, full_name, phone_number, hashed_password, is_active, is_verified, etc.

#### Projects
- Escrow project/transaction records
- Status tracking: draft, pending, active, completed, disputed, etc.
- Links creator, buyer, and seller (all users)
- Financial fields: total_amount, currency

#### Milestones
- Project deliverables and payment milestones
- Linked to projects (cascade delete)
- Status tracking: pending, in_progress, completed, approved, etc.
- Payment tracking: is_paid, paid_at

#### Transactions
- Financial transaction records
- Links to users and projects
- FinCra payment gateway integration
- Types: deposit, withdrawal, escrow_hold, escrow_release, refund, fee, commission
- Status tracking: pending, processing, completed, failed, etc.

## Running Migrations

### Prerequisites

1. Set up your environment variables in `.env`:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_KEY=your-supabase-service-key
   ```

### Commands

#### Apply all pending migrations
```bash
alembic upgrade head
```

#### Rollback the last migration
```bash
alembic downgrade -1
```

#### Rollback all migrations
```bash
alembic downgrade base
```

#### Check current migration version
```bash
alembic current
```

#### View migration history
```bash
alembic history
```

#### Generate a new migration (auto-detect changes)
```bash
alembic revision --autogenerate -m "Description of changes"
```

#### Create an empty migration
```bash
alembic revision -m "Description of changes"
```

## Row-Level Security (RLS)

The migrations include RLS policies for Supabase. These policies use `auth.uid()` to identify the authenticated user.

### Policy Overview

**Users Table:**
- Users can read and update their own records
- No public read/write access

**Projects Table:**
- Users can read projects where they are creator, buyer, or seller
- Only creators can create, update, and delete projects

**Milestones Table:**
- Users can read milestones for projects they're involved in
- Only project creators can manage milestones

**Transactions Table:**
- Users can only read and create their own transactions
- Updates/deletes are restricted (should be done via system functions)

### Important Notes for Supabase

1. **Auth Integration**: RLS policies use `auth.uid()` which requires Supabase Auth to be set up
2. **Service Role**: Some operations may need the service role key to bypass RLS
3. **Testing**: When testing locally, you may need to disable RLS or create appropriate test users

## Async Database Support

The migrations are configured for async operations:
- Uses `asyncio.run()` for running migrations
- Compatible with async SQLAlchemy engine
- Works with `asyncpg` driver

## Development Workflow

1. **Make model changes** in `app/models/`
2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Description"
   ```
3. **Review the generated migration** in `alembic/versions/`
4. **Test the migration**:
   ```bash
   alembic upgrade head
   ```
5. **If there are issues**, rollback and fix:
   ```bash
   alembic downgrade -1
   # Fix the migration file
   alembic upgrade head
   ```

## Troubleshooting

### Connection Issues
- Verify `DATABASE_URL` is correct in `.env`
- Ensure PostgreSQL is running and accessible
- Check firewall and network settings

### RLS Issues
- RLS policies require Supabase Auth setup
- For local development, you may need to temporarily disable RLS
- Use service role key for admin operations

### Migration Conflicts
- If you have multiple migration branches, use:
  ```bash
  alembic branches
  alembic merge <revisions> -m "Merge branches"
  ```

## Best Practices

1. **Always backup** your database before running migrations in production
2. **Test migrations** on a staging environment first
3. **Review auto-generated migrations** - they may need manual adjustments
4. **Keep migrations small** and focused on specific changes
5. **Document complex migrations** with comments
6. **Never modify** existing migrations that have been applied to production
7. **Use meaningful names** for migration messages
