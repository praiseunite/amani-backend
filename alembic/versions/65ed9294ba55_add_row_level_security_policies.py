"""Add Row-Level Security policies

Revision ID: 65ed9294ba55
Revises: 68db6a7fba94
Create Date: 2025-11-10 07:27:51.945039

This migration adds Row-Level Security (RLS) policies for Supabase PostgreSQL.
RLS ensures that users can only access and modify their own data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65ed9294ba55'
down_revision: Union[str, None] = '68db6a7fba94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable Row-Level Security on all tables."""
    
    # Enable RLS on users table
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    
    # Users can read their own data
    op.execute("""
        CREATE POLICY users_select_own 
        ON users FOR SELECT 
        USING (auth.uid() = id)
    """)
    
    # Users can update their own data
    op.execute("""
        CREATE POLICY users_update_own 
        ON users FOR UPDATE 
        USING (auth.uid() = id)
    """)
    
    # Enable RLS on projects table
    op.execute("ALTER TABLE projects ENABLE ROW LEVEL SECURITY")
    
    # Users can read projects they're involved in (creator, buyer, or seller)
    op.execute("""
        CREATE POLICY projects_select_involved 
        ON projects FOR SELECT 
        USING (
            auth.uid() = creator_id OR 
            auth.uid() = buyer_id OR 
            auth.uid() = seller_id
        )
    """)
    
    # Users can insert projects if they are the creator
    op.execute("""
        CREATE POLICY projects_insert_creator 
        ON projects FOR INSERT 
        WITH CHECK (auth.uid() = creator_id)
    """)
    
    # Users can update projects they created
    op.execute("""
        CREATE POLICY projects_update_creator 
        ON projects FOR UPDATE 
        USING (auth.uid() = creator_id)
    """)
    
    # Users can delete projects they created
    op.execute("""
        CREATE POLICY projects_delete_creator 
        ON projects FOR DELETE 
        USING (auth.uid() = creator_id)
    """)
    
    # Enable RLS on milestones table
    op.execute("ALTER TABLE milestones ENABLE ROW LEVEL SECURITY")
    
    # Users can read milestones for projects they're involved in
    op.execute("""
        CREATE POLICY milestones_select_involved 
        ON milestones FOR SELECT 
        USING (
            EXISTS (
                SELECT 1 FROM projects 
                WHERE projects.id = milestones.project_id 
                AND (
                    auth.uid() = projects.creator_id OR 
                    auth.uid() = projects.buyer_id OR 
                    auth.uid() = projects.seller_id
                )
            )
        )
    """)
    
    # Users can insert milestones for projects they created
    op.execute("""
        CREATE POLICY milestones_insert_creator 
        ON milestones FOR INSERT 
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM projects 
                WHERE projects.id = milestones.project_id 
                AND auth.uid() = projects.creator_id
            )
        )
    """)
    
    # Users can update milestones for projects they created
    op.execute("""
        CREATE POLICY milestones_update_creator 
        ON milestones FOR UPDATE 
        USING (
            EXISTS (
                SELECT 1 FROM projects 
                WHERE projects.id = milestones.project_id 
                AND auth.uid() = projects.creator_id
            )
        )
    """)
    
    # Users can delete milestones for projects they created
    op.execute("""
        CREATE POLICY milestones_delete_creator 
        ON milestones FOR DELETE 
        USING (
            EXISTS (
                SELECT 1 FROM projects 
                WHERE projects.id = milestones.project_id 
                AND auth.uid() = projects.creator_id
            )
        )
    """)
    
    # Enable RLS on transactions table
    op.execute("ALTER TABLE transactions ENABLE ROW LEVEL SECURITY")
    
    # Users can read their own transactions
    op.execute("""
        CREATE POLICY transactions_select_own 
        ON transactions FOR SELECT 
        USING (auth.uid() = user_id)
    """)
    
    # Users can insert their own transactions
    op.execute("""
        CREATE POLICY transactions_insert_own 
        ON transactions FOR INSERT 
        WITH CHECK (auth.uid() = user_id)
    """)
    
    # Note: Transactions typically shouldn't be updated or deleted by users
    # Updates should be done by system/admin functions only


def downgrade() -> None:
    """Disable Row-Level Security and remove policies."""
    
    # Drop policies for transactions
    op.execute("DROP POLICY IF EXISTS transactions_insert_own ON transactions")
    op.execute("DROP POLICY IF EXISTS transactions_select_own ON transactions")
    op.execute("ALTER TABLE transactions DISABLE ROW LEVEL SECURITY")
    
    # Drop policies for milestones
    op.execute("DROP POLICY IF EXISTS milestones_delete_creator ON milestones")
    op.execute("DROP POLICY IF EXISTS milestones_update_creator ON milestones")
    op.execute("DROP POLICY IF EXISTS milestones_insert_creator ON milestones")
    op.execute("DROP POLICY IF EXISTS milestones_select_involved ON milestones")
    op.execute("ALTER TABLE milestones DISABLE ROW LEVEL SECURITY")
    
    # Drop policies for projects
    op.execute("DROP POLICY IF EXISTS projects_delete_creator ON projects")
    op.execute("DROP POLICY IF EXISTS projects_update_creator ON projects")
    op.execute("DROP POLICY IF EXISTS projects_insert_creator ON projects")
    op.execute("DROP POLICY IF EXISTS projects_select_involved ON projects")
    op.execute("ALTER TABLE projects DISABLE ROW LEVEL SECURITY")
    
    # Drop policies for users
    op.execute("DROP POLICY IF EXISTS users_update_own ON users")
    op.execute("DROP POLICY IF EXISTS users_select_own ON users")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
