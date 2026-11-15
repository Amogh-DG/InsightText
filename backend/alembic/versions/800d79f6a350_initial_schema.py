from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '800d79f6a350'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('system_settings',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('value', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_settings_key'), 'system_settings', ['key'], unique=True)
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('api_keys',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('key_hash', sa.String(length=255), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_table('audit_logs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=True),
    sa.Column('action', sa.String(length=255), nullable=False),
    sa.Column('detail', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('datasets',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner_id', sa.String(length=36), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=False),
    sa.Column('text_column', sa.String(length=255), nullable=False),
    sa.Column('label_column', sa.String(length=255), nullable=True),
    sa.Column('time_column', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('documents',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('text_encrypted', sa.Text(), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('meta', sa.JSON(), nullable=False),
    sa.Column('processed', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('model_versions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('algorithm', sa.String(length=100), nullable=False),
    sa.Column('feature_type', sa.String(length=50), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=True),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('artifact_path', sa.String(length=500), nullable=False),
    sa.Column('metrics', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_by', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('topics',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('keywords', sa.JSON(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('analyses',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('document_id', sa.String(length=36), nullable=False),
    sa.Column('sentiment_label', sa.String(length=50), nullable=False),
    sa.Column('sentiment_score', sa.Float(), nullable=False),
    sa.Column('entities', sa.JSON(), nullable=False),
    sa.Column('intent', sa.String(length=100), nullable=False),
    sa.Column('intent_score', sa.Float(), nullable=False),
    sa.Column('topic_id', sa.String(length=36), nullable=True),
    sa.Column('low_confidence', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('predictions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('model_version_id', sa.String(length=36), nullable=True),
    sa.Column('document_id', sa.String(length=36), nullable=True),
    sa.Column('input_text_encrypted', sa.Text(), nullable=False),
    sa.Column('predicted_label', sa.String(length=255), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('probabilities', sa.JSON(), nullable=False),
    sa.Column('created_by', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feedbacks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('prediction_id', sa.String(length=36), nullable=False),
    sa.Column('corrected_label', sa.String(length=255), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('reviewer_id', sa.String(length=36), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('feedbacks')
    op.drop_table('predictions')
    op.drop_table('analyses')
    op.drop_table('topics')
    op.drop_table('model_versions')
    op.drop_table('documents')
    op.drop_table('datasets')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_system_settings_key'), table_name='system_settings')
    op.drop_table('system_settings')
