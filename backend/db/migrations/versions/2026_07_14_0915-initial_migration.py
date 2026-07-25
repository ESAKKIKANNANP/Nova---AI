"""Initial migration schema for Users, Projects, Datasets, PipelineRuns, ModelArtifacts, Reports, and ChatHistories.

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-07-14 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'users' table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # 2. Create 'projects' table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_projects_owner_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_projects')
    )
    op.create_index('ix_projects_id', 'projects', ['id'], unique=False)

    # 3. Create 'datasets' table
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('storage_uri', sa.String(length=512), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('schema_metadata', sa.JSON(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_datasets_project_id_projects', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_datasets')
    )
    op.create_index('ix_datasets_id', 'datasets', ['id'], unique=False)

    # 4. Create 'pipeline_runs' table
    op.create_table(
        'pipeline_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('plan', sa.JSON(), nullable=True),
        sa.Column('execution_logs', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('runtime_metrics', sa.JSON(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], name='fk_pipeline_runs_dataset_id_datasets', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_pipeline_runs_project_id_projects', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_pipeline_runs')
    )
    op.create_index('ix_pipeline_runs_id', 'pipeline_runs', ['id'], unique=False)

    # 5. Create 'model_artifacts' table
    op.create_table(
        'model_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('hyperparameters', sa.JSON(), nullable=True),
        sa.Column('evaluation_metrics', sa.JSON(), nullable=True),
        sa.Column('feature_importance', sa.JSON(), nullable=True),
        sa.Column('storage_uri', sa.String(length=512), nullable=False),
        sa.Column('is_deployed', sa.Boolean(), nullable=False),
        sa.Column('deployment_endpoint', sa.String(length=512), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], name='fk_model_artifacts_pipeline_run_id_pipeline_runs', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_model_artifacts_project_id_projects', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_model_artifacts')
    )
    op.create_index('ix_model_artifacts_id', 'model_artifacts', ['id'], unique=False)

    # 6. Create 'reports' table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('content_markdown', sa.Text(), nullable=True),
        sa.Column('file_format', sa.String(length=50), nullable=False),
        sa.Column('storage_uri', sa.String(length=512), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], name='fk_reports_pipeline_run_id_pipeline_runs', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_reports_project_id_projects', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_reports')
    )
    op.create_index('ix_reports_id', 'reports', ['id'], unique=False)

    # 7. Create 'chat_histories' table
    op.create_table(
        'chat_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender', sa.String(length=50), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('additional_metadata', sa.JSON(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_chat_histories_project_id_projects', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_chat_histories')
    )
    op.create_index('ix_chat_histories_id', 'chat_histories', ['id'], unique=False)
    op.create_index('ix_chat_histories_session_id', 'chat_histories', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_chat_histories_session_id', table_name='chat_histories')
    op.drop_index('ix_chat_histories_id', table_name='chat_histories')
    op.drop_table('chat_histories')

    op.drop_index('ix_reports_id', table_name='reports')
    op.drop_table('reports')

    op.drop_index('ix_model_artifacts_id', table_name='model_artifacts')
    op.drop_table('model_artifacts')

    op.drop_index('ix_pipeline_runs_id', table_name='pipeline_runs')
    op.drop_table('pipeline_runs')

    op.drop_index('ix_datasets_id', table_name='datasets')
    op.drop_table('datasets')

    op.drop_index('ix_projects_id', table_name='projects')
    op.drop_table('projects')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
