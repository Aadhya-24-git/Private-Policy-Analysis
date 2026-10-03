"""initial_tables

Revision ID: 0001_initial_tables
Revises: 
Create Date: 2026-10-03 15:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '0001_initial_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. documents table
    op.create_table(
        'documents',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column(
            'source_type',
            sa.Enum('pdf', 'docx', 'txt', 'text', 'web', name='source_type_enum'),
            nullable=False,
        ),
        sa.Column('upload_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'processing', 'indexed', 'analyzed', 'failed', name='document_status_enum'),
            nullable=False,
        ),
    )
    op.create_index('ix_documents_source_type', 'documents', ['source_type'])
    op.create_index('ix_documents_upload_time', 'documents', ['upload_time'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_upload_time_status', 'documents', ['upload_time', 'status'])

    # 2. clauses table
    op.create_table(
        'clauses',
        sa.Column('clause_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'document_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('documents.document_id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('paragraph_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(length=255), nullable=True),
        sa.Column('clause_text', sa.Text(), nullable=False),
        sa.Column('clause_order', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
    )
    op.create_index('ix_clauses_document_id', 'clauses', ['document_id'])
    op.create_index('ix_clauses_doc_order', 'clauses', ['document_id', 'clause_order'])

    # 3. findings table
    op.create_table(
        'findings',
        sa.Column('finding_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'clause_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('clauses.clause_id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column(
            'risk_level',
            sa.Enum('low', 'medium', 'high', 'critical', name='risk_level_enum'),
            nullable=False,
        ),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('validated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_findings_clause_id', 'findings', ['clause_id'])
    op.create_index('ix_findings_category', 'findings', ['category'])
    op.create_index('ix_findings_risk_level', 'findings', ['risk_level'])
    op.create_index('ix_findings_validated', 'findings', ['validated'])
    op.create_index('ix_findings_created_at', 'findings', ['created_at'])
    op.create_index('ix_findings_risk_category', 'findings', ['risk_level', 'category'])

    # 4. chat_history table
    op.create_table(
        'chat_history',
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'document_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('documents.document_id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_chat_history_document_id', 'chat_history', ['document_id'])
    op.create_index('ix_chat_history_created_at', 'chat_history', ['created_at'])
    op.create_index('ix_chat_history_doc_created', 'chat_history', ['document_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('chat_history')
    op.drop_table('findings')
    op.drop_table('clauses')
    op.drop_table('documents')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS risk_level_enum;")
    op.execute("DROP TYPE IF EXISTS document_status_enum;")
    op.execute("DROP TYPE IF EXISTS source_type_enum;")
