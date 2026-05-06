"""Initial prediction tables

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
    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('image_path', sa.Text(), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('image_size_bytes', sa.Integer(), nullable=True),
        sa.Column('predicted_class', sa.String(255), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('is_malignant', sa.Boolean(), nullable=True),
        sa.Column('top_predictions', postgresql.JSON(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_predictions_user_id', 'predictions', ['user_id'])
    op.create_index('ix_predictions_status', 'predictions', ['status'])
    op.create_index('ix_predictions_celery_task_id', 'predictions', ['celery_task_id'])
    op.create_index('ix_predictions_created_at', 'predictions', ['created_at'])

    # Create prediction_feedback table
    op.create_table(
        'prediction_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('predictions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('actual_class', sa.String(255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_prediction_feedback_prediction_id', 'prediction_feedback', ['prediction_id'])
    op.create_index('ix_prediction_feedback_user_id', 'prediction_feedback', ['user_id'])


def downgrade() -> None:
    op.drop_table('prediction_feedback')
    op.drop_table('predictions')
