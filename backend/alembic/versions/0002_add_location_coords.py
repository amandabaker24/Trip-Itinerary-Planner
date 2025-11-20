"""add latitude longitude to locations

Revision ID: 0002_add_location_coords
Revises: 0001_create_core_tables
Create Date: 2025-11-20 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_location_coords"
down_revision = "0001_create_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("locations") as batch_op:
        batch_op.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("locations") as batch_op:
        batch_op.drop_column("longitude")
        batch_op.drop_column("latitude")
