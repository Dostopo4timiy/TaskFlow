"""initial migration

Revision ID: initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    task_status_enum = postgresql.ENUM(
        'new', 'pending', 'in_progress', 'completed', 'failed', 'cancelled',
        name='task_status_enum'
    )
    task_status_enum.create(op.get_bind())
    
    task_priority_enum = postgresql.ENUM(
        'low', 'medium', 'high',
        name='task_priority_enum'
    )
    task_priority_enum.create(op.get_bind())
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', task_priority_enum, nullable=False),
        sa.Column('status', task_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_info', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    
    # Drop enum types
    op.execute('DROP TYPE task_status_enum')
    op.execute('DROP TYPE task_priority_enum')
