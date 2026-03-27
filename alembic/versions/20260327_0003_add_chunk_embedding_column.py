"""add embedding column to document chunks

Revision ID: 20260327_0003
Revises: 20260327_0002
Create Date: 2026-03-27

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260327_0003"
down_revision: str | None = "20260327_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding vector(256)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_ivfflat "
        "ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_ivfflat")
    op.execute("ALTER TABLE document_chunks DROP COLUMN embedding")
