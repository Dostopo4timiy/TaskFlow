"""initial

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание enum типов
    task_status = postgresql.ENUM(
        'NEW', 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED',
        name='taskstatus'
    )
    task_status.create(op.get_bind())
    
    task_priority = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH',
        name='taskpriority'
    )
    task_priority.create(op.get_bind())
    
    # Создание таблицы tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', task_priority, nullable=True),
        sa.Column('status', task_status, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_info', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    
    # Удаление enum типов
    task_status = postgresql.ENUM(
        'NEW', 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED',
        name='taskstatus'
    )
    task_status.drop(op.get_bind())
    
    task_priority = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH',
        name='taskpriority'
    )
    task_priority.drop(op.get_bind())
