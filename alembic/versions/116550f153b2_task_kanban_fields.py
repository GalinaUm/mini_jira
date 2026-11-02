"""task kanban fields

Revision ID: 116550f153b2
Revises: 6fa22d546d69
Create Date: 2026-11-02 10:15:56.621220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '116550f153b2'
down_revision: Union[str, Sequence[str], None] = '6fa22d546d69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('description', sa.Text(), nullable=True))

    op.alter_column(
        'tasks',
        'due_time',
        new_column_name='due_date',
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )

    op.alter_column(
        'tasks',
        'assignee_id',
        existing_type=sa.UUID(),
        nullable=True,
    )

    op.drop_constraint('tasks_assignee_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key(
        'tasks_assignee_id_fkey',
        'tasks',
        'users',
        ['assignee_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('UPDATE tasks SET assignee_id = created_by_id WHERE assignee_id IS NULL')
    op.execute('UPDATE tasks SET due_date = now() WHERE due_date IS NULL')

    op.drop_constraint('tasks_assignee_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key(
        'tasks_assignee_id_fkey',
        'tasks',
        'users',
        ['assignee_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.alter_column(
        'tasks',
        'assignee_id',
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.alter_column(
        'tasks',
        'due_date',
        new_column_name='due_time',
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.drop_column('tasks', 'description')
