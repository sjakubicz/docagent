from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("content", sa.LargeBinary(), nullable=True))
    op.add_column(
        "pages", sa.Column("ocr", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.alter_column("pages", "ocr", server_default=None)
    op.execute(
        "UPDATE pages SET ocr = true FROM documents "
        "WHERE pages.document_id = documents.id AND documents.ocr_pages = documents.num_pages "
        "AND documents.num_pages > 0"
    )


def downgrade() -> None:
    op.drop_column("pages", "ocr")
    op.drop_column("documents", "content")
