"""add egress_id to interview_sessions

Revision ID: a1b2c3d4e5f6
Revises: 9bbeb0372a86
Create Date: 2026-03-09 21:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "9bbeb0372a86"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions", sa.Column("egress_id", sa.String(255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("interview_sessions", "egress_id")
