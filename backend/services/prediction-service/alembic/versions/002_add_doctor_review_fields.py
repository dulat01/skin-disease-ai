"""Add doctor review fields and user_message

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('predictions', sa.Column('user_message', sa.Text(), nullable=True))
    op.add_column('predictions', sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('predictions', sa.Column('doctor_approved', sa.Boolean(), nullable=True))
    op.add_column('predictions', sa.Column('doctor_notes', sa.Text(), nullable=True))
    op.add_column('predictions', sa.Column('doctor_reviewed_at', sa.DateTime(), nullable=True))
    op.create_index('ix_predictions_doctor_id', 'predictions', ['doctor_id'])


def downgrade() -> None:
    op.drop_index('ix_predictions_doctor_id', 'predictions')
    op.drop_column('predictions', 'doctor_reviewed_at')
    op.drop_column('predictions', 'doctor_notes')
    op.drop_column('predictions', 'doctor_approved')
    op.drop_column('predictions', 'doctor_id')
    op.drop_column('predictions', 'user_message')
