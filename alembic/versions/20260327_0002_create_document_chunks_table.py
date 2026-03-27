"""create document chunks table

Revision ID: 20260327_0002
Revises: 20260326_0001
Create Date: 2026-03-27

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260327_0002"
down_revision: str | None = "20260326_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_document_chunks"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_order"),
    )
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
