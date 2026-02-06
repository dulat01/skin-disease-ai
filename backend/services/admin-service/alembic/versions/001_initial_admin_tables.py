"""Initial admin tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create daily_statistics table
    op.create_table(
        'daily_statistics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('total_users', sa.Integer(), default=0),
        sa.Column('new_users', sa.Integer(), default=0),
        sa.Column('active_users', sa.Integer(), default=0),
        sa.Column('total_predictions', sa.Integer(), default=0),
        sa.Column('successful_predictions', sa.Integer(), default=0),
        sa.Column('failed_predictions', sa.Integer(), default=0),
        sa.Column('avg_processing_time_ms', sa.Float(), nullable=True),
        sa.Column('disease_distribution', postgresql.JSON(), nullable=True),
        sa.Column('malignant_count', sa.Integer(), default=0),
        sa.Column('benign_count', sa.Integer(), default=0),
        sa.Column('feedback_count', sa.Integer(), default=0),
        sa.Column('positive_feedback', sa.Integer(), default=0),
        sa.Column('negative_feedback', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_daily_statistics_date', 'daily_statistics', ['date'])

    # Create model_metrics table
    op.create_table(
        'model_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_predictions', sa.Integer(), default=0),
        sa.Column('avg_confidence', sa.Float(), nullable=True),
        sa.Column('min_confidence', sa.Float(), nullable=True),
        sa.Column('max_confidence', sa.Float(), nullable=True),
        sa.Column('feedback_count', sa.Integer(), default=0),
        sa.Column('correct_predictions', sa.Integer(), default=0),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('class_metrics', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_model_metrics_model_version', 'model_metrics', ['model_version'])
    op.create_index('ix_model_metrics_date', 'model_metrics', ['date'])

    # Create admin_notifications table
    op.create_table(
        'admin_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('is_dismissed', sa.Boolean(), default=False),
        sa.Column('extra_data', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_admin_notifications_type', 'admin_notifications', ['type'])
    op.create_index('ix_admin_notifications_created_at', 'admin_notifications', ['created_at'])


def downgrade() -> None:
    op.drop_table('admin_notifications')
    op.drop_table('model_metrics')
    op.drop_table('daily_statistics')
