from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("status", sa.String(20), server_default="ready", nullable=False),
    )
    op.add_column("documents", sa.Column("error", sa.Text(), nullable=True))
    op.alter_column("documents", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("documents", "error")
    op.drop_column("documents", "status")
