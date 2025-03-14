"""create schedule


Revision ID: e9baf9389777
Revises:
Create Date: 2025-03-14 15:04:35.590758

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e9baf9389777"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "schedules",
        sa.Column("medicine_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("intake_period", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("treatment_duration", sa.Interval(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "schedule_datetime", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("schedules")
    # ### end Alembic commands ###
