"""initialize extra

Revision ID: 60884f7304da
Revises: 1a31ce608336
Create Date: 2025-01-12 08:43:32.172643

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '60884f7304da'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('celery_taskmeta',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.String(length=155), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('result', sa.PickleType(), nullable=True),
        sa.Column('date_done', sa.DateTime(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('name', sa.String(length=155), nullable=True),
        sa.Column('args', sa.LargeBinary(), nullable=True),
        sa.Column('kwargs', sa.LargeBinary(), nullable=True),
        sa.Column('worker', sa.String(length=155), nullable=True),
        sa.Column('retries', sa.Integer(), nullable=True),
        sa.Column('queue', sa.String(length=155), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id'),
        sqlite_autoincrement=True
    )
    op.create_table('celery_tasksetmeta',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('taskset_id', sa.String(length=155), nullable=True),
        sa.Column('result', sa.PickleType(), nullable=True),
        sa.Column('date_done', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('taskset_id'),
        sqlite_autoincrement=True
    )


def downgrade():
    op.drop_table('celery_tasksetmeta')
    op.drop_table('celery_taskmeta')
