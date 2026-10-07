"""embed_dim_1024

Revision ID: 0002_embed_dim_1024
Revises: 0001_initial_tables
Create Date: 2026-10-03 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_embed_dim_1024'
down_revision: Union[str, None] = '0001_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely alter vector dimension from 1536 to 1024 in PostgreSQL pgvector.
    # By specifying USING NULL, we preserve all existing rows, documents, clauses,
    # findings, and chat history while preventing 1536/1024 dimension corruption.
    # Existing clauses will be re-embedded with qwen3-embedding:0.6b (1024-dim).
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE clauses ALTER COLUMN embedding TYPE vector(1024) USING NULL;")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE clauses ALTER COLUMN embedding TYPE vector(1536) USING NULL;")
